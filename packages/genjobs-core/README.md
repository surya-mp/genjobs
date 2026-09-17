# genjobs-core

The dependency-free core of the GenJobs ecosystem. It provides job lifecycle
models, idempotency, task registration, a portable worker engine, and protocols
for job stores, queues, and artifact stores.

Install it when you are implementing a custom backend or want no infrastructure
dependencies:

```bash
python -m pip install genjobs-core
```

`GenJobs` requires implementations of all three protocols. For local work,
install `genjobs-local`; for production, choose only the integration packages
appropriate to your infrastructure.

The authoritative architecture and API documentation live in the repository’s
[`docs/`](../../docs) directory.
