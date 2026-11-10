"""Public sample-user lookup used only by the internal acceptance fixture."""
from contextlib import closing
import os
import sqlite3

from flask import Flask, jsonify, request

app = Flask(__name__)
app.config["DATABASE"] = os.environ["APP_DATABASE"]


@app.get("/users")
def users():
    """Return exact-name matches as a JSON array of id/name objects."""
    name = request.args.get("name", "")
    query = "SELECT id, name FROM users WHERE name = '" + name + "' ORDER BY id"
    with closing(sqlite3.connect(app.config["DATABASE"])) as connection:
        records = connection.execute(query).fetchall()
    return jsonify([{"id": row[0], "name": row[1]} for row in records])
