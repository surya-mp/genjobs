# GenJobs

GenJobs is an Apache-2.0-licensed, provider-neutral Python package ecosystem
for building asynchronous, long-running job APIs. It is not a model platform:
it does not host models, run GPUs, receive user data, or require a cloud
account. Teams install only the pieces they need and connect them to their own
infrastructure.

It applies equally to text, images, audio, video, multi-modal workflows, batch
ML, document rendering, browser automation, scientific computation, and other
jobs that may take time and produce temporary artifacts.

## Packages

| Distribution | Import | Purpose | Dependencies |
| --- | --- | --- | --- |
| `genjobs-core` | `genjobs_core` | Stable job contracts, task execution engine, and backend protocols. | None |
| `genjobs-local` | `genjobs_local` | In-memory queue/store and local-disk artifacts for development and tests. | `genjobs-core` |

## Package boundaries

`genjobs-core` owns portable domain concepts only: jobs, task handlers,
idempotency, lifecycle state, and the small queue/job-store/artifact-store
protocols. It deliberately has no infrastructure implementation.

`genjobs-local` is an explicitly non-production backend that lets developers
exercise the same contracts locally. Teams can implement the core protocols
against their own infrastructure without adopting a GenJobs cloud wrapper.

Read [the documentation](docs/index.md) for the architecture, public API,
backend authoring contract, security model, and release process.

## Repository development

Requires Python 3.11+ and a virtual environment.

```bash
python -m pip install -e packages/genjobs-core -e packages/genjobs-local
python -m pip install pytest pytest-asyncio ruff pyright build twine
ruff check .
pyright
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.
Maintainers should follow [PUBLISHING.md](PUBLISHING.md) for PyPI setup and
release steps.
