<!-- last-verified: 2026-08-02 against 7a4cedf (master) -->

# DictionaryAuthenticator

**LIVE — do not delete.** Modernized 2026-08-02 to v1.0.0: PEP 621 packaging, dynamic version,
GitHub Actions CI (py3.10–3.13), 18 tests, `jupyterhub>=4`, Python 3.9+.

It looks abandoned — one commit for five years, 18 lines of code. It is in production for the
Executive Education cohort, which uses shared team logins rather than university SSO.

## Where this fits

Username/password auth against a plain dict supplied in config. No external service, no database,
no file — the credential store *is* the traitlets `passwords` dict.

**My half of the contract:** none. No wire protocol. One trait, `passwords`.

**Who consumes me:** pip-installed from this GitHub default branch, **unpinned**, by
`images/hub/Dockerfile:10` in `darden-data-science/jupyterhub-config-darden`. Selected by
`config_files/exec-ed/values.yaml:54` as `authenticator_class:
DictionaryAuthenticator.DictionaryAuthenticator` — that cohort's `values.yaml` layers last, so it
wins over the `authType: dummy` the master helmfile passes it.

**Full system map:** `/Users/Michael/Documents/Git Projects/Darden Jupyterhub/docs/SYSTEM-MAP.md`
(repo `darden-data-science/jupyterhub-config-darden`, private).

## Two rosters, and why that matters here

Unlike `../NullAuthenticator`, this authenticator **can** succeed, so JupyterHub's allow gate is
live. On JupyterHub 5 `allow_all` defaults to `False`, meaning a correct password is necessary but
not sufficient — the user must also be in `allowed_users`.

exec-ed therefore maintains **two hand-edited lists in the same file**:
`Authenticator.allowed_users` (`config_files/exec-ed/values.yaml:24`) and
`DictionaryAuthenticator.passwords` (line 55). Drift between them fails confusingly in both
directions, and neither failure says the rosters disagree.

**v1.0.0 logs a warning at startup when they disagree** (`_warn_on_roster_drift`). It stays a
warning, not an error: `allowed_users` legitimately holds admins who authenticate another way, and
`allow_all = True` skips the check entirely.

**[J] Verified 2026-08-02: the live exec-ed roster is consistent** — 28 users, 28 allowed, no
drift. A correct password authenticates, a wrong one and an unknown user are both denied, checked
by loading the real `values.yaml` through the package.

## Commands

```bash
uv venv && uv pip install -e ".[dev]"
```

```bash
uv run python -m unittest discover -s tests -v
```

## Testing convention — deliberately different from ExternalAuthenticator

Tests run against a **real JupyterHub**, not the `sys.modules`-stubbed pattern in
`../ExternalAuthenticator`. What matters here is the interaction with JupyterHub's own allow gate
— a user can authenticate and still be denied — which only exists in a real JupyterHub.

Note `assertLogs` must target the logger named **`traitlets`**, not `DictionaryAuthenticator`.
Traitlets' `LoggingConfigurable.log` defaults to the former; asserting on the class name silently
never matches and the test passes for the wrong reason.

## Changes in v1.0.0 beyond packaging

- `secrets.compare_digest` instead of `==`, with both sides encoded to UTF-8 first — a non-ASCII
  password previously raised `TypeError` rather than failing to match.
- `data.get()` instead of `data['username']` — any caller other than the built-in login form used
  to raise a bare `KeyError`, surfacing as a 500.
- Non-string values in `passwords` (YAML turns bare `1234` into an int) now fail closed.
- The roster drift warning above.

`authenticate()` remains `async def`, unlike `../NullAuthenticator`'s sync version. Both are valid;
JupyterHub calls through `maybe_future()`.

## Known issues

- **Its `passwords` dict is ~28 plaintext `username: password` pairs committed to
  `config_files/exec-ed/values.yaml`, which is NOT SOPS-encrypted.** They are already in git
  history, so redacting the file does not undo the exposure. Treat credential rotation as a
  prerequisite for any exec-ed work.
- The hub image installs from this branch unpinned, so merging to `master` lands in the next hub
  image build, and `ENV cacheBuster` in `images/hub/Dockerfile` must be bumped or Docker serves
  the cached layer.
