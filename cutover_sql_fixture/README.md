# Internal SQL lookup acceptance fixture

This directory deliberately contains a SQL-injection weakness for an internal
remediation acceptance run. Its sample database contains public example names.

`GET /users?name=Alice` returns HTTP200 and `[{"id":1,"name":"Alice"}]`.
A name with no exact match returns HTTP200 and `[]`. Results contain only `id`
and `name` and are ordered by id. The endpoint must match the complete input as
one literal name; input must never change the SQL expression or expose other rows.
Preserve the route, response shape, ordering, and legitimate exact-name behavior.
The fix can parameterize the lookup without changing the database schema.

The database contract is owned by `initialize.py`: table `users`, integer primary
key `id`, non-null text `name`. The initializer refuses to replace an existing
file. The runtime must receive `APP_DATABASE` naming this pre-created SQLite file;
missing configuration is a startup error, not a request to invent another database.
No external identity provider, templates, secret, or protocol counterpart is required.

For local fixture inspection, from this directory:

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python initialize.py --database data/users.sqlite3
APP_DATABASE=data/users.sqlite3 .venv/bin/flask --app app run --host 127.0.0.1 --port 8000
```

The local inspection server uses loopback without debug mode. These commands are
an internal fixture contract. Source analysis does not require running a server.
Run the ordinary API contract examples with `python -m unittest -v test_contract`.
