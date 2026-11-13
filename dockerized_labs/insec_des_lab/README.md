# Serialization round-trip fixture

This internal test fixture contains the forms referenced by `main.py`. The
application source is unchanged; these files complete the previously missing
browser path.

- [Index form](templates/index.html) posts `username` to `/serialize`, or
  `serialized_data` to `/deserialize`.
- [Result form](templates/result.html) displays the serializer's output and posts
  that same opaque value to `/deserialize`. Neither template decodes the value.
- Responses display the application's user message with normal HTML escaping.
- The fixture contains no serialized-payload storage or separate client codec.

[Round-trip tests](test_round_trip.py) exercise the existing route/form contract
with ordinary, quoted, Unicode and HTML-containing usernames, plus malformed
input. They do not depend on a particular serialization implementation.

Use the Flask runtime declared by the repository. From the repository root:

```sh
python -m unittest discover -s dockerized_labs/insec_des_lab -p 'test_*.py'
```

This is an intentionally vulnerable security test application. The round-trip
tests establish its ordinary behavior; the targeted security scan separately
identifies unsafe deserialization.
