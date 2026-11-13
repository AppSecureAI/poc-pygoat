import ast
import operator
import os
import sqlite3
import subprocess

import yaml
from flask import Flask, jsonify, request

app = Flask(__name__)
app.config["SECRET_KEY"] = "ledger-signing-key-2024"

DATABASE = os.path.join(os.path.dirname(__file__), "ledger.db")


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


@app.route("/accounts/<owner>")
def account_lookup(owner):
    rows = get_db().execute(
        "SELECT id, owner, balance FROM accounts WHERE owner = '%s'" % owner
    ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.route("/filters", methods=["POST"])
def apply_filters():
    try:
        filters = parse_filters(request.form.get("filters", "{}"))
        return jsonify({"filters": filters})
    except (SyntaxError, ValueError, TypeError, ArithmeticError, RecursionError):
        app.logger.warning("Invalid filter expression rejected")
        return jsonify({"error": "Invalid filter expression"}), 400


def parse_filters(expression):
    # Resource limits follow filter_contract.json.
    if len(expression) > 65536:
        raise ValueError("Expression limit exceeded")
    tree = ast.parse(expression.strip(), mode="eval")
    for count, _ in enumerate(ast.walk(tree), 1):
        if count > 1024:
            raise ValueError("Node limit exceeded")
    remaining = 65536
    max_integer = (1 << 4096) - 1
    operations = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }

    def charge(units):
        nonlocal remaining
        if units > remaining:
            raise ValueError("Expansion limit exceeded")
        remaining -= units

    def multiply(left, right):
        if isinstance(left, int) and isinstance(right, int):
            if right and abs(left) > max_integer // abs(right):
                raise ValueError("Integer limit exceeded")
        return left * right

    def power(left, right):
        if not isinstance(left, int) or not isinstance(right, int) or right < 0:
            return left ** right
        if right == 0 or left == 1:
            return 1
        if left == 0:
            return 0
        if left == -1:
            return -1 if right % 2 else 1
        if right >= 4096:
            raise ValueError("Integer limit exceeded")
        result = 1
        while right:
            if right & 1:
                result = multiply(result, left)
            right >>= 1
            if right:
                left = multiply(left, left)
        return result

    def visit(node, depth=0):
        if depth > 64:
            raise ValueError("Depth limit exceeded")
        units = 1
        if isinstance(node, ast.Constant):
            value = node.value
            if type(value) not in (str, int, float, bool, type(None)):
                raise ValueError("Unsupported literal")
            if isinstance(value, str):
                units = max(1, len(value))
        elif isinstance(node, (ast.List, ast.Tuple)):
            items = [visit(item, depth + 1) for item in node.elts]
            units = 1 + sum(size for _, size in items)
            charge(units)
            values = [value for value, _ in items]
            return (tuple(values) if isinstance(node, ast.Tuple) else values), units
        elif isinstance(node, ast.Dict):
            items = [(visit(key, depth + 1), visit(value, depth + 1))
                     for key, value in zip(node.keys, node.values)]
            units = 1 + sum(key[1] + value[1] for key, value in items)
            charge(units)
            return {key[0]: value[0] for key, value in items}, units
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            operand, _ = visit(node.operand, depth + 1)
            if not isinstance(operand, (int, float)):
                raise ValueError("Unsupported operand")
            value = +operand if isinstance(node.op, ast.UAdd) else -operand
        elif isinstance(node, ast.BinOp) and type(node.op) in operations:
            left, left_size = visit(node.left, depth + 1)
            right, right_size = visit(node.right, depth + 1)
            if isinstance(node.op, ast.Add) and type(left) in (str, list, tuple) and type(left) is type(right):
                units = max(1, len(left) + len(right)) if isinstance(left, str) else left_size + right_size - 1
                charge(units)
                return left + right, units
            if isinstance(node.op, ast.Mult):
                sequence, size, count = left, left_size, right
                if isinstance(left, int):
                    sequence, size, count = right, right_size, left
                if isinstance(sequence, (str, list, tuple)) and isinstance(count, int):
                    count = max(0, count)
                    units = max(1, len(sequence) * count) if isinstance(sequence, str) else 1 + (size - 1) * count
                    charge(units)
                    return sequence * count, units
            if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
                raise ValueError("Unsupported operands")
            if isinstance(node.op, ast.Mult):
                value = multiply(left, right)
            elif isinstance(node.op, ast.Pow):
                value = power(left, right)
            else:
                value = operations[type(node.op)](left, right)
            if not isinstance(value, (int, float)):
                raise ValueError("Unsupported result")
        else:
            raise ValueError("Unsupported expression")
        if isinstance(value, int):
            if value.bit_length() > 4096:
                raise ValueError("Integer limit exceeded")
            units = max(1, (value.bit_length() + 7) // 8)
        charge(units)
        return value, units

    return visit(tree.body)[0]


@app.route("/archive", methods=["POST"])
def archive():
    name = request.form.get("name", "ledger")
    subprocess.run("tar -czf /var/backups/%s.tgz ledger.db" % name, shell=True, check=True)
    return jsonify({"status": "archived"})


@app.route("/rules", methods=["POST"])
def import_rules():
    rules = yaml.load(request.data, Loader=yaml.Loader)
    return jsonify({"rules": len(rules or [])})
