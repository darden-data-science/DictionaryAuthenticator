# DictionaryAuthenticator

A JupyterHub `Authenticator` that checks credentials against a dict of
`username: password` supplied in config. No database, no external service, no file — the
credential store *is* the config.

Adapted from the [example in the JupyterHub documentation](https://jupyterhub.readthedocs.io/en/stable/reference/authenticators.html#authenticator-authenticate-method),
packaged for pip.

**Scope:** small shared-login cohorts — team accounts on a short course, a workshop, a demo hub.
Not identity management. Passwords live in whatever holds your JupyterHub config, in plaintext,
which is fine for a week-long exec-ed session and unacceptable for anything else.

## Install

```bash
pip install git+https://github.com/darden-data-science/DictionaryAuthenticator.git
```

## Use

```python
c.JupyterHub.authenticator_class = "dictionary_authenticator"

c.DictionaryAuthenticator.passwords = {
    "team1": "correct-horse",
    "team2": "battery-staple",
}

# Required on JupyterHub 5+ — see below.
c.Authenticator.allowed_users = {"team1", "team2"}
```

The dotted path `"DictionaryAuthenticator.DictionaryAuthenticator"` works too, and is what
Zero-to-JupyterHub deployments generally use.

Full example: [`examples/jupyterhub_config.example.py`](examples/jupyterhub_config.example.py).

## Two rosters, one cohort

This is the thing that wastes an afternoon.

Authenticating is **necessary but not sufficient**. JupyterHub 5 defaults
`Authenticator.allow_all` to `False`, so after this authenticator accepts a password, JupyterHub
still checks the user against `allowed_users`. That means two lists, maintained by hand, usually
in separate blocks of the same file:

| Drift | What the user sees |
|---|---|
| In `allowed_users`, missing from `passwords` | No password ever matches. Login just fails, with no explanation. |
| In `passwords`, missing from `allowed_users` | Password accepted, then denied at the gate. Looks like a broken account. |

Neither says *"your two rosters disagree."* So this package logs a warning at startup when they
do. It stays a warning rather than an error, because `allowed_users` legitimately holds admins who
authenticate some other way — and setting `allow_all = True` makes the comparison moot, in which
case the check is skipped entirely.

## Compatibility

Python 3.10+, JupyterHub 4.x and 5.x.

Passwords are compared with `secrets.compare_digest` rather than `==`. Both sides are encoded to
UTF-8 first, because `compare_digest` raises `TypeError` on non-ASCII `str` — so a password with
an accent in it used to crash rather than fail to match.

This does not hide *whether a username exists*: a miss in `passwords` returns early. That is
deliberate. These deployments keep passwords in plaintext in the config anyway; padding the timing
of a username probe would be ceremony, not security.

A non-string value in `passwords` (YAML turns a bare `1234` into an int) fails closed rather than
raising.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md).

```bash
pip install -e ".[dev]" && python -m unittest discover -s tests -v
```

## License

BSD 3-Clause. See [LICENSE](LICENSE).
