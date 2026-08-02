<!-- last-verified: 2026-08-02 against 28ef6c1 (master) -->

# DictionaryAuthenticator

**LIVE — do not delete.** 18 lines of code and exactly **one commit ever** (2020-08-05). No tests,
no CI, `setup.py` only, `python_requires>=3.5`, `jupyterhub>=1.1.0`.

It looks abandoned. It is in production for the Executive Education cohort, which uses shared team
logins rather than university SSO.

## Where this fits

Username/password auth against a plain dict supplied in config. No external service, no database,
no file — the credential store *is* the traitlets `passwords` dict. `authenticate()` is a single
equality check.

**My half of the contract:** none. No wire protocol. One trait, `passwords`.

**Who consumes me:** pip-installed from this GitHub default branch, **unpinned**, by
`images/hub/Dockerfile:10` in `darden-data-science/jupyterhub-config-darden`. Selected by
`config_files/exec-ed/values.yaml:54` as `authenticator_class:
DictionaryAuthenticator.DictionaryAuthenticator` — that cohort's `values.yaml` layers last, so it
wins over the `authType: dummy` the master helmfile passes it.

**Full system map:** `/Users/Michael/Documents/Git Projects/Darden Jupyterhub/docs/SYSTEM-MAP.md`
(repo `darden-data-science/jupyterhub-config-darden`, private).

## Known issues

- **Its `passwords` dict is supplied as ~28 plaintext `username: password` pairs committed to
  `config_files/exec-ed/values.yaml`, which is NOT SOPS-encrypted.** They are already in git
  history, so redacting the file does not undo the exposure. Treat credential rotation as a
  prerequisite for any exec-ed work.
- **JupyterHub 5 `allow_all`.** `DictionaryAuthenticator.py:16` returns a bare username string
  with no `check_allowed` override. The exec-ed deployment satisfies the JupyterHub 5 requirement
  via `Authenticator.allowed_users` (`config_files/exec-ed/values.yaml:24`) rather than
  `allow_all` — but **that list and the `passwords` dict at line 55 are maintained separately and
  by hand.** A user present in one and not the other fails confusingly. Change both together on
  every roster update.
- `DictionaryAuthenticator.py:15` indexes `data['username']` / `data['password']` directly —
  bare `KeyError` on malformed input. Fine for the built-in login form, fragile otherwise.
- Password comparison uses `==`, not a constant-time compare. Minor here, worth a note.
- `DictionaryAuthenticator/__pycache__/` contains a stale `NullAuthenticator.cpython-38.pyc` —
  this package was copied from `../NullAuthenticator`.
- No `pyproject.toml`. Modernization template is `../ExternalAuthenticator`; the
  `sys.modules`-stubbed unittest pattern there suits an 18-line package particularly well.
