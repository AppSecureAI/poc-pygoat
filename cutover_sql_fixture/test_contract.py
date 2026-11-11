"""Executable examples of the sample lookup's legitimate public behavior."""
import os
from pathlib import Path
import tempfile
import unittest

from initialize import initialize


class LookupContract(unittest.TestCase):
    """Check ordinary exact matches and missing names against real SQLite."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        database = Path(self.directory.name) / "users.sqlite3"
        initialize(database)
        previous = os.environ.get("APP_DATABASE")
        os.environ["APP_DATABASE"] = str(database)
        self.addCleanup(self.restore_environment, previous)
        from app import app
        app.config.update(TESTING=True)
        self.client = app.test_client()

    @staticmethod
    def restore_environment(previous):
        if previous is None:
            os.environ.pop("APP_DATABASE", None)
        else:
            os.environ["APP_DATABASE"] = previous

    def test_exact_name_match(self):
        response = self.client.get("/users", query_string={"name": "Alice"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [{"id": 1, "name": "Alice"}])

    def test_missing_name(self):
        response = self.client.get("/users", query_string={"name": "Nobody"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])


if __name__ == "__main__":
    unittest.main()
