# Ledger filter behavior

`POST /filters` reads the `filters` form field and returns `{"filters": result}`. Omitting the field returns an empty dictionary. The original application accepts Python literal syntax, ordinary arithmetic, and sequence concatenation/repetition, including nested dictionaries and lists.

The regression tests preserve concrete, harmless examples of that existing behavior. In particular, repeated strings/lists and the tested integer powers must continue to work. These examples do not authorize arbitrary function calls, attribute access or unbounded resource use; a safe replacement must reject executable constructs and apply resource limits without rejecting the tested values.

Run the ordinary behavior tests with `python -m unittest discover -s dockerized_labs/ledger_service -p 'test_filter_contract.py' -k FilterContractTests`. They pass against the original application. The security tests intentionally fail against the original unsafe implementation and must pass after repair. Run both groups by omitting `-k FilterContractTests`.

These tests exercise the real Flask route. They do not prescribe a parser, implementation, or new dependency.
