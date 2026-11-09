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
    filters = eval(request.form.get("filters", "{}"))
    return jsonify({"filters": filters})


@app.route("/archive", methods=["POST"])
def archive():
    name = request.form.get("name", "ledger")
    subprocess.run("tar -czf /var/backups/%s.tgz ledger.db" % name, shell=True, check=True)
    return jsonify({"status": "archived"})


@app.route("/rules", methods=["POST"])
def import_rules():
    rules = yaml.load(request.data, Loader=yaml.Loader)
    return jsonify({"rules": len(rules or [])})
