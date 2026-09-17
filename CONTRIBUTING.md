# Contributing

Thank you for contributing. GenJobs keeps its core deliberately small so that
applications can choose infrastructure without inheriting unrelated packages.

## Development setup

Use Python 3.11 or newer in an isolated virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e packages/genjobs-core -e packages/genjobs-local
python -m pip install pytest pytest-asyncio ruff pyright build twine
```

Before a pull request, run:

```bash
ruff format --check .
ruff check .
pyright
pytest
python -m build packages/genjobs-core
python -m build packages/genjobs-local
twine check packages/genjobs-core/dist/* packages/genjobs-local/dist/*
```

Remove generated `dist/` directories after local release checks; they are never
committed.

## Package boundary rules

- `genjobs-core` remains dependency-free and cannot import a backend, web
  framework, cloud SDK, model SDK, or environment-specific configuration.
- A backend is a separate distribution and implements the core protocols.
- Optional integrations may depend on `genjobs-core`, but never on each other
  unless the dependency is essential and documented.
- Do not add model-specific logic to core. Model adapters are separate packages.
- Public API changes require documentation, tests, and a changelog entry.

## Pull requests

Keep pull requests focused. Include the user-facing reason, compatibility
impact, tests, and docs. New integrations should include a minimal example and
state their data retention, retry, authentication, and cleanup behavior.

## Versioning and releases

Each distribution is versioned independently under SemVer. A breaking change to
the core protocol requires a new core major version; integration packages must
then publish a compatible version range. Releases are made from signed `v*`
tags after CI passes and PyPI Trusted Publishing is configured.

By contributing, you agree that your contribution is licensed under Apache-2.0.
