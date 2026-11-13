# Ledger filter behavior

`POST /filters` reads the `filters` form field and returns `{"filters": result}`. Omitting the field returns an empty dictionary. The original application accepts Python literal syntax, ordinary arithmetic, and sequence concatenation/repetition, including nested dictionaries and lists.

The regression tests preserve concrete, harmless examples of that existing behavior. In particular, repeated strings/lists and the tested integer powers must continue to work. These examples do not authorize arbitrary function calls, attribute access or unbounded resource use; a safe replacement must reject executable constructs and apply resource limits without rejecting the tested values.

Run the ordinary behavior tests with `python -m unittest discover -s dockerized_labs/ledger_service -p 'test_filter_contract.py' -k FilterContractTests`. They pass against the original application. The security tests intentionally fail against the original unsafe implementation and must pass after repair. Run both groups by omitting `-k FilterContractTests`.

These tests exercise the real Flask route. They do not prescribe a parser, implementation, or new dependency.

## Repair input policy for this internal fixture

The prospective repair contract is specified by [filter_contract.json](filter_contract.json). The intentionally vulnerable baseline does not enforce it. Security repair is explicitly allowed to reject previously accepted expressions outside this profile; unrestricted Python execution and unlimited computation are not compatibility requirements.

The profile permits 65,536 expression characters, 1,024 Python AST nodes, traversal depth 64 (root value at depth zero), and integers of at most 4,096 bits. Inputs exactly at a limit remain supported when their other properties and aggregate cost are valid. The tests include positive and negative boundary cases.

A total expansion budget of 65,536 estimated resource units may cover parsed values, intermediate results and expanded collections. Conservative charges may count both an intermediate and its containing result. It is acceptable to reject an expression whose small final output nevertheless requires excessive intermediate work. Multiplication and nested expansion must be checked before large allocations; numeric operations must be bounded before disproportionate computation.

Unsupported executable constructs and out-of-policy expressions must return HTTP 400 with a JSON object containing a nonempty, generic `error` string. Rejection logs must not echo submitted values. The ordinary behavior examples remain required. Implement the operators and limits generally; do not special-case test strings or weaken the tests/profile to obtain a passing result.

This is an explicit, prospective acceptance policy for the internal test application. It does not establish the input requirements of any other application. The remediation must preserve this profile; changing it is a separate contract change. Run all behavior, security and boundary tests with `python -m unittest discover -s dockerized_labs/ledger_service -p 'test_filter_contract.py'`.
