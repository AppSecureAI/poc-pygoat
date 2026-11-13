"""Exercise the actual forms without depending on their serialization format."""
import importlib.util
import base64
import json
from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


class PageContent(HTMLParser):
    """Collect rendered text and opaque form values from real HTML responses."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text = []
        self.values = []
        self._reading_value = False

    def handle_starttag(self, tag, attrs):
        if tag == "textarea" and dict(attrs).get("name") == "serialized_data":
            self._reading_value = True

    def handle_endtag(self, tag):
        if tag == "textarea":
            self._reading_value = False

    def handle_data(self, data):
        self.text.append(data)
        if self._reading_value:
            self.values.append(data)


class SerializationRoundTripTests(unittest.TestCase):
    """Check the browser form contract through the real Flask application."""

    @classmethod
    def setUpClass(cls):
        """Load the same application module for both sides of each round trip."""
        path = Path(__file__).with_name("main.py")
        spec = importlib.util.spec_from_file_location("serialization_fixture_app", path)
        if spec is None or spec.loader is None:
            raise RuntimeError("Application module is unavailable")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        module.app.config.update(TESTING=True)
        cls.client = module.app.test_client()

    def round_trip(self, data, expected_name):
        """Forward the serializer's opaque form value to the deserializer."""
        serialized = self.client.post("/serialize", data=data)
        self.assertEqual(serialized.status_code, 200)
        page = PageContent()
        page.feed(serialized.get_data(as_text=True))
        value = "".join(page.values)
        self.assertTrue(value)
        result = self.client.post("/deserialize", data={"serialized_data": value})
        self.assertEqual(result.status_code, 200)
        rendered = result.get_data(as_text=True)
        page = PageContent()
        page.feed(rendered)
        self.assertIn("Welcome " + expected_name + ".", "".join(page.text))
        self.assertIn("Only admins can see the secret content.", "".join(page.text))
        return rendered

    def test_index_contains_both_form_inputs(self):
        """The landing page exposes both existing form endpoints."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        self.assertIn('name="username"', text)
        self.assertIn('name="serialized_data"', text)

    def test_ordinary_quoted_and_unicode_usernames(self):
        """User data survives the actual serialize/render/post/deserialize path."""
        for name in ("alice", "O'Brian", "Zoë雪"):
            with self.subTest(username=name):
                self.round_trip({"username": name}, name)

    def test_default_username(self):
        """Omitting the username preserves the application's guest default."""
        self.round_trip({}, "guest")

    def test_html_username_is_escaped(self):
        """The rendered result displays user text without executable markup."""
        name = "<script>alert(1)</script>"
        rendered = self.round_trip({"username": name}, name)
        self.assertNotIn("<script>", rendered)
        self.assertIn("&lt;script&gt;", rendered)

    def test_malformed_payload_returns_an_application_error(self):
        """Malformed input remains a handled response rather than a server crash."""
        with self.assertLogs(self.client.application.logger, level="WARNING") as logs:
            response = self.client.post("/deserialize", data={"serialized_data": "not valid data"})
        self.assertIn(response.status_code, (200, 400))
        self.assertIn("Error: Invalid user data", response.get_data(as_text=True))
        self.assertEqual([record.getMessage() for record in logs.records],
                         ["Invalid user data submitted for deserialization"])

    def test_pickle_payload_is_not_executed(self):
        """Executable pickle instructions remain inert input."""
        payload = base64.b64encode(b"cbuiltins\nprint\n(S'deserialization executed'\ntR.").decode()
        with patch("builtins.print") as output:
            response = self.client.post("/deserialize", data={"serialized_data": payload})
        output.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Error", response.get_data(as_text=True))

    def test_invalid_user_fields_are_rejected(self):
        """JSON values must describe a user with the expected field types."""
        for value in ([], {}, {"username": []}, {"username": "alice", "is_admin": "false"}):
            with self.subTest(value=value):
                payload = base64.b64encode(json.dumps(value).encode()).decode()
                response = self.client.post("/deserialize", data={"serialized_data": payload})
                self.assertEqual(response.status_code, 200)
                self.assertIn("Invalid user data", response.get_data(as_text=True))

    def test_unsupported_fields_do_not_disclose_input(self):
        """Unsupported fields cannot appear in responses or warning logs."""
        field = "private-field\r\nforged-log-entry"
        payload = base64.b64encode(json.dumps({"username": "alice", field: "private-value"}).encode()).decode()
        with self.assertLogs(self.client.application.logger, level="WARNING") as logs:
            response = self.client.post("/deserialize", data={"serialized_data": payload})
        self.assertEqual(response.status_code, 200)
        page = PageContent()
        page.feed(response.get_data(as_text=True))
        text = "".join(page.text)
        self.assertIn("Invalid user data", text)
        self.assertNotIn("private-field", text)
        self.assertNotIn("private-value", text)
        self.assertNotIn("TypeError", text)
        self.assertEqual([record.getMessage() for record in logs.records],
                         ["Invalid user data submitted for deserialization"])


if __name__ == "__main__":
    unittest.main()
