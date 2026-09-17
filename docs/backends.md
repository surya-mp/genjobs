# Backend authoring guide

Each backend is a separate Python distribution. It must depend on a compatible
`genjobs-core` version and implement one or more protocols from
`genjobs_core.protocols`.

## Required behavior

### Job store

- Create and retrieve jobs durably.
- Preserve state, timestamps, attempt count, output, error, and artifacts.
- Find a job by idempotency key.
- Use optimistic locking, transactions, or equivalent concurrency protection.

### Queue

- Enqueue a job identifier only; do not place large payloads or artifacts in
  messages.
- Define acknowledgement and visibility/retry semantics.
- Handle duplicate delivery: workers must treat a job already terminal as a no-op.

### Artifact store

- Copy a local worker file to controlled storage.
- Return an opaque artifact reference with an explicit expiry.
- Delete by artifact ID/reference and provide expiry cleanup.
- Document encryption, access control, signed URL duration, and deletion
  guarantees.

## Suggested package layout

```text
genjobs-sqs/
  pyproject.toml
  src/genjobs_sqs/
    queue.py
    job_store.py
  tests/
```

Publish integrations independently. Do not make a cloud SDK an optional extra
inside `genjobs-core`; separate distributions give users predictable installs
and independent security upgrades.

## Compatibility policy

Declare an upper bound on `genjobs-core`, for example
`genjobs-core>=0.1,<0.2`. Test against the lowest supported core version and
the newest release. Bump the integration’s major version if its own public API
breaks.

## Reliability baseline

Do not add cloud or model SDK wrappers to core merely for convenience. An
integration belongs in core only if it defines a provider-independent baseline
that improves reliability or compatibility for all users. Examples include a
durable delivery contract, portable artifact semantics, or a standard model
worker protocol. Provider credentials, cloud setup, SDK clients, and model
implementation details stay in the application or a separate project.

Production backends must test atomic idempotency creation, duplicate delivery,
delayed retries, worker heartbeats, lease expiry, cancellation requests,
artifact access control, expiry cleanup, and crash recovery. `genjobs-local` is
only a reference implementation and is intentionally not a production backend.
