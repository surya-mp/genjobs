# Core API guide

Install `genjobs-core` for the portable interfaces. It has no runtime
dependencies.

## Construction

`GenJobs` requires three implementations supplied by the application:

```python
from genjobs_core import GenJobs

engine = GenJobs(artifacts=artifact_store, jobs=job_store, queue=queue)
```

`job_store` implements durable job state, `queue` carries job IDs to workers,
and `artifact_store` writes output files. The protocols are structural, so a
class does not need to inherit from a GenJobs base class.

## Registering a task

```python
from genjobs_core import ArtifactInput, ContentKind, TaskContext, TaskResult


@engine.task("image.generate")
async def generate_image(context: TaskContext, payload: dict[str, object]) -> TaskResult:
    await context.progress(0.1, "loading model")
    # Validate payload, invoke application-owned code, then write a temp file.
    return TaskResult(
        output={"seed": 42},
        files=[
            ArtifactInput(
                path="/tmp/output.png",
                kind=ContentKind.IMAGE,
                media_type="image/png",
            )
        ],
    )
```

A handler returns `TaskResult`. `output` is small structured metadata stored
with the job; `files` are worker-local paths that the configured artifact store
copies to its controlled location. Task errors are captured as failed job state.
Applications that need domain-specific errors should record a safe message and
keep sensitive stack traces in private logs.

## Submitting and running

```python
from genjobs_core import JobRequest

job = await engine.submit(
    JobRequest(
        task="image.generate",
        payload={"prompt": "sunset over a lake"},
        idempotency_key="request-123",
        artifact_ttl_seconds=3600,
    )
)

# A pull-worker process calls this after obtaining work from its queue.
completed = await engine.run_next()

# A push queue or HTTP worker endpoint runs a known job ID directly.
completed = await engine.run(job.id)
```

`submit` returns the existing job when an idempotency key is already known.
`run_next` is intentionally small and useful for a local worker loop. A
production adapter may invoke it after SQS, Redis, Cloud Tasks, or another
queue delivers a job ID. Duplicate delivery must be safe at the job-store level.

## State and cancellation

Use `await engine.get(job_id)` to retrieve state. Job states are `queued`,
`running`, `succeeded`, `failed`, and `cancelled`. `cancel` only cancels queued
jobs. Interrupting a running model is provider-specific and must be implemented
cooperatively by an integration or task runtime.

## Local development

Install `genjobs-local` for `InMemoryJobStore`, `InMemoryJobQueue`, and
`LocalArtifactStore`. Those implementations are intentionally process-local;
they do not guarantee durability, distributed locking, or multi-worker safety.
