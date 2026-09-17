# GenJobs documentation

GenJobs is a composable library ecosystem for a common application problem:
turning long-running work into reliable asynchronous jobs without tying the
application to a specific cloud, queue, artifact store, model runtime, or
modality.

It does not host or operate models for users. A team owns its workers, model
licenses, compute, credentials, data, and retention policy. GenJobs makes the
application-facing and worker-facing plumbing consistent.

## Install only what you use

```bash
# Contracts and execution engine only
python -m pip install genjobs-core

# Add local test/development backends
python -m pip install genjobs-local
```

There is intentionally no umbrella package. Applications implement the stable
core protocols directly for their own web framework, cloud, queue, object store,
and model runtime. This prevents dependency and vendor lock-in.

## Core flow

```text
application -> JobRequest -> job store + queue -> worker -> artifact store -> application
```

The application submits a named task. A worker receives its job ID from a queue,
executes the registered handler, persists progress and result state, and puts
optional output files into the chosen artifact store. The application then
polls or is notified through its own API layer.

Read [concepts](concepts.md) before implementing a backend, then follow
[backend authoring](backends.md). The core package’s API is documented in the
[API guide](api.md). For modality-neutral input and output conventions, see
[modalities](modalities.md).

Maintainers can use the [publishing guide](publishing.md) for PyPI configuration
and release steps.
