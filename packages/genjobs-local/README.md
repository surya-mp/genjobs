# genjobs-local

Dependency-free in-memory and local-disk implementations of the GenJobs core
protocols. It is for development, examples, and tests—not multi-process or
production deployments.

```bash
python -m pip install genjobs-local
```

It provides `InMemoryJobStore`, `InMemoryJobQueue`, and `LocalArtifactStore`.
For production, use a durable queue, job store, and artifact store integration
that matches your own infrastructure.
