# Concepts and lifecycle

## Job request

`JobRequest` contains a task name, JSON-like payload, typed input asset
references, an optional idempotency key, a maximum attempt count, and an
artifact TTL. The package does not inspect model prompts or understand a
provider-specific request schema; that belongs to the task owner. A failed task
is re-queued until `max_attempts` is reached; backends may add delayed or
dead-letter retry policies.

An idempotency key represents one logical request. When the same key is
submitted again, the engine returns the existing job rather than enqueueing
duplicate expensive work. Stores must make this lookup/create operation safe
under concurrent requests in production.

## Job states

```text
queued -> running -> succeeded
                 -> failed
queued -> cancelled
```

Terminal jobs never transition again. A queued job can be cancelled. Running
tasks need cooperative cancellation support from their worker/runtime; core
does not interrupt arbitrary Python or GPU code.

## Tasks

A task is a function registered under a stable name. It receives a
`TaskContext` and a payload dictionary, reports progress from 0 to 1, and
returns `TaskResult`. Files in `TaskResult.files` are copied into the configured
artifact store and become `Artifact` records with an expiry timestamp. Input and
output references carry a coarse `ContentKind` (text, image, audio, video,
file, or structured) plus an optional MIME type; those values are descriptive,
not a validation or conversion layer.

Task handlers should be deterministic where possible, validate their own
payloads, avoid logging sensitive input, and use a unique temporary work
directory. They should never assume a local artifact store or a particular
cloud SDK.

## Artifacts and retention

An artifact is a reference, not bytes stored in the job record. Artifact stores
must enforce `expires_at`, support explicit deletion, and avoid returning
publicly guessable locations. The local backend is only a convenience for tests;
production adapters should use signed URLs or authenticated retrieval.

The TTL starts when a job writes an artifact. Applications that require no
durable outputs should delete artifacts after their consuming operation and run
scheduled expiry cleanup as a backstop.
