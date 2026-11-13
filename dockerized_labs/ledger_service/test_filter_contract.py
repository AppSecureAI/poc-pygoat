"""Exercise the public filter route without depending on its evaluator implementation."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


class FilterApplicationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).with_name("app.py")
        spec = importlib.util.spec_from_file_location("ledger_filter_contract", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        module.app.config.update(TESTING=True)
        cls.application = module.app

    def setUp(self):
        self.client = self.application.test_client()

    def assert_filter(self, expression, expected):
        response = self.client.post("/filters", data={"filters": expression})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"filters": expected})


class FilterContractTests(FilterApplicationTestCase):
    def test_default_is_empty_dictionary(self):
        response = self.client.post("/filters", data={})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"filters": {}})

    def test_literal_collections_and_usernames(self):
        for value in ({"owner": "O'Brian", "active": True, "extra": None},
                      {"owner": "Zoë雪", "amounts": [1, 2.5]}, ["owner", 2, False]):
            with self.subTest(value=value):
                self.assert_filter(repr(value), value)

    def test_numeric_operators_and_nested_values(self):
        for expression, expected in (("{'minimum': 1 + 2}", {"minimum": 3}),
                ("(10 - 4) * 3", 18), ("9 / 2", 4.5), ("9 // 2", 4),
                ("9 % 2", 1), ("-3 + +2", -1), ("2 ** 10", 1024)):
            with self.subTest(expression=expression):
                self.assert_filter(expression, expected)

    def test_sequence_concatenation(self):
        for expression, expected in (("'ab' + 'cd'", "abcd"),
                                     ("[1] + [2]", [1, 2])):
            with self.subTest(expression=expression):
                self.assert_filter(expression, expected)

    def test_string_repetition(self):
        self.assert_filter("'a' * 2", "aa")

    def test_reversed_string_repetition(self):
        self.assert_filter("2 * 'a'", "aa")

    def test_list_repetition(self):
        self.assert_filter("[1, 2] * 2", [1, 2, 1, 2])

    def test_safe_integer_power(self):
        self.assert_filter("2 ** 2049", 2 ** 2049)

    def test_safe_integer_power_boundary(self):
        self.assert_filter("2 ** 4095", 2 ** 4095)


class FilterSecurityTests(FilterApplicationTestCase):
    def test_function_calls_are_inert(self):
        with patch("builtins.print", return_value=None) as output:
            response = self.client.post("/filters", data={"filters": "print('inert test marker')"})
        output.assert_not_called()
        self.assertIn(response.status_code, (400, 422))

    def test_attribute_access_is_rejected(self):
        response = self.client.post("/filters", data={"filters": "().__class__.__name__"})
        self.assertIn(response.status_code, (400, 422))


if __name__ == "__main__":
    unittest.main()
