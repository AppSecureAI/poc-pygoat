"""Create the explicit sample database without replacing an existing file."""
import argparse
from contextlib import closing
from pathlib import Path
import sqlite3


def initialize(database):
    """Initialize one new database with the public sample lookup contract."""
    path = Path(database)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb"):
        pass
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        connection.executemany("INSERT INTO users (id, name) VALUES (?, ?)", [(1, "Alice"), (2, "Bob")])
        connection.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True)
    initialize(parser.parse_args().database)
