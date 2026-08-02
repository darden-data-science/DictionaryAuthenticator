# Contributing

## Setup

Either works. `uv` is faster and is what the sibling repos in this system use.

```bash
uv venv && uv pip install -e ".[dev]"
```

```bash
python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
```

## Tests

```bash
uv run python -m unittest discover -s tests -v
```

These run against a **real JupyterHub**, which `[project.dependencies]` installs. That is a
deliberate difference from the sibling `ExternalAuthenticator` repo, which stubs `jupyterhub` and
`traitlets` into `sys.modules` so its tests run with no dependencies.

The reason: what matters here is the interaction with JupyterHub's own allow gate — a user can
authenticate successfully and still be denied — and that only exists in a real JupyterHub. A
stubbed one would report success against a broken package.

## Build

```bash
uv run python -m build
```

## Releasing

The version lives in exactly one place: `DictionaryAuthenticator/_version.py`. `pyproject.toml` reads it
via `[tool.setuptools.dynamic]`, so bump the tuple there and nothing else.

Uncomment the `'dev'` element for a development version; leave it commented for a release.

## Downstream impact

The Darden JupyterHub hub image installs this package **from GitHub's default branch, unpinned**
(`images/hub/Dockerfile` in `darden-data-science/jupyterhub-config-darden`). Anything merged to
`master` lands in the next hub image build.

Two consequences:

1. Merging is a deploy decision, not just a code decision.
2. Docker layer-caches that `pip install`, so `ENV cacheBuster` in the hub Dockerfile has to be
   bumped or the rebuild silently keeps the old version.

This authenticator carries **live exec-ed credentials**. A regression locks out a running cohort,
and the passwords are plaintext in the config repo, so credential rotation is a prerequisite for
any change to that deployment.
