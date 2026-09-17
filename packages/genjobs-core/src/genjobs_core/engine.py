"""A portable orchestration engine built on the package protocols."""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import suppress
from datetime import timedelta
from pathlib import Path

from .errors import InvalidStateTransitionError, TaskNotFoundError
from .events import JobEvent, JobObserver
from .models import ArtifactInput, Job, JobRequest, JobStatus, utcnow
from .protocols import ArtifactStore, JobQueue, JobStore
from .serialization import request_size_bytes
from .tasks import TaskContext, TaskRegistry


class GenJobs:
    """Coordinates jobs but has no knowledge of models, clouds, or GPUs."""

    def __init__(
        self,
        *,
        artifacts: ArtifactStore,
        jobs: JobStore,
        queue: JobQueue,
        observers: Sequence[JobObserver] = (),
        max_payload_bytes: int = 1_000_000,
    ) -> None:
        self.artifacts = artifacts
        self.jobs = jobs
        self.queue = queue
        self.tasks = TaskRegistry()
        self.observers = tuple(observers)
        if max_payload_bytes < 1:
            raise ValueError("max_payload_bytes must be at least 1")
        self.max_payload_bytes = max_payload_bytes

    def task(self, name: str):
        """Register a task handler with ``@jobs.task('name')``."""
        return self.tasks.register(name)

    async def submit(self, request: JobRequest) -> Job:
        if request_size_bytes(request) > self.max_payload_bytes:
            raise ValueError(f"job payload exceeds {self.max_payload_bytes} bytes")
        if request.idempotency_key:
            existing = await self.jobs.find_by_idempotency_key(request.idempotency_key)
            if existing:
                return existing
        job = await self.jobs.create(Job.from_request(request))
        await self.queue.enqueue(job.id)
        await self._emit("submitted", job)
        return job

    async def get(self, job_id: str) -> Job:
        return await self.jobs.get(job_id)

    async def cancel(self, job_id: str) -> Job:
        job = await self.jobs.get(job_id)
        if job.status is JobStatus.RUNNING:
            job.cancel_requested = True
            job.message = "cancellation requested"
            job.refresh()
            updated = await self.jobs.update(job)
            await self._emit("cancellation_requested", updated)
            return updated
        if job.status.is_terminal:
            raise InvalidStateTransitionError(f"cannot cancel a {job.status} job")
        job.status = JobStatus.CANCELLED
        job.message = "cancelled before execution"
        job.refresh()
        updated = await self.jobs.update(job)
        await self._emit("cancelled", updated)
        return updated

    async def run_next(self) -> Job | None:
        """Run one queued job. Cloud workers can invoke this in a polling loop."""
        job_id = await self.queue.dequeue()
        if job_id is None:
            return None
        return await self.run(job_id)

    async def run(self, job_id: str) -> Job:
        """Run a known job ID, for push queues and HTTP worker endpoints."""
        job = await self.jobs.get(job_id)
        if job.status.is_terminal or job.status is JobStatus.RUNNING:
            return job
        handler = self.tasks.get(job.request.task)
        if handler is None:
            job.status = JobStatus.FAILED
            job.error = str(TaskNotFoundError(job.request.task))
            job.refresh()
            return await self.jobs.update(job)

        job.status = JobStatus.RUNNING
        job.attempt += 1
        job.retry_at = None
        job.heartbeat_at = utcnow()
        job.message = "running"
        job.refresh()
        await self.jobs.update(job)
        await self._emit("started", job)

        async def update_progress(value: float, message: str | None) -> None:
            job.progress = value
            job.message = message
            job.heartbeat_at = utcnow()
            job.refresh()
            await self.jobs.update(job)
            await self._emit("progress", job)

        async def is_cancel_requested() -> bool:
            return (await self.jobs.get(job.id)).cancel_requested

        try:
            result = await self.tasks.call(
                job.request.task,
                TaskContext(job, update_progress, is_cancel_requested),
                job.request.payload,
            )
            if await is_cancel_requested():
                job.status = JobStatus.CANCELLED
                job.message = "cancelled by task"
                job.refresh()
                updated = await self.jobs.update(job)
                await self._emit("cancelled", updated)
                return updated
            job.artifacts = [await self._store_artifact(job, item) for item in result.files]
            job.output = result.output
            job.progress = 1.0
            job.status = JobStatus.SUCCEEDED
            job.message = "completed"
            job.refresh()
            await self._emit("succeeded", job)
        except Exception as error:
            job.error = f"{type(error).__name__}: {error}"
            if job.attempt < job.request.max_attempts:
                delay_seconds = job.request.retry_policy.delay_for_attempt(job.attempt)
                job.status = JobStatus.QUEUED
                job.retry_at = utcnow() + timedelta(seconds=delay_seconds)
                job.message = f"retrying in {delay_seconds:g}s"
                job.refresh()
                await self.jobs.update(job)
                await self.queue.enqueue(job.id, delay_seconds=delay_seconds)
                await self._emit("retry_scheduled", job)
                return job
            job.status = JobStatus.FAILED
            job.message = "failed"
            job.refresh()
            await self._emit("failed", job)
        return await self.jobs.update(job)

    async def _emit(self, name: str, job: Job) -> None:
        event = JobEvent(
            name=name,
            job_id=job.id,
            task=job.request.task,
            status=job.status,
            attempt=job.attempt,
            occurred_at=utcnow(),
            progress=job.progress,
            message=job.message,
        )
        for observer in self.observers:
            with suppress(Exception):
                await observer.on_event(event)

    async def _store_artifact(self, job: Job, item: ArtifactInput):
        source = Path(item.path)
        return await self.artifacts.put_file(
            source,
            name=item.name or source.name,
            kind=item.kind,
            media_type=item.media_type,
            expires_at=job.artifact_expiry(),
        )
