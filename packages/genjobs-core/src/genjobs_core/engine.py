"""A portable orchestration engine built on the package protocols."""

from __future__ import annotations

from pathlib import Path

from .errors import InvalidStateTransitionError, TaskNotFoundError
from .models import ArtifactInput, Job, JobRequest, JobStatus
from .protocols import ArtifactStore, JobQueue, JobStore
from .tasks import TaskContext, TaskRegistry


class GenJobs:
    """Coordinates jobs but has no knowledge of models, clouds, or GPUs."""

    def __init__(
        self,
        *,
        artifacts: ArtifactStore,
        jobs: JobStore,
        queue: JobQueue,
    ) -> None:
        self.artifacts = artifacts
        self.jobs = jobs
        self.queue = queue
        self.tasks = TaskRegistry()

    def task(self, name: str):
        """Register a task handler with ``@jobs.task('name')``."""
        return self.tasks.register(name)

    async def submit(self, request: JobRequest) -> Job:
        if request.idempotency_key:
            existing = await self.jobs.find_by_idempotency_key(request.idempotency_key)
            if existing:
                return existing
        job = await self.jobs.create(Job.from_request(request))
        await self.queue.enqueue(job.id)
        return job

    async def get(self, job_id: str) -> Job:
        return await self.jobs.get(job_id)

    async def cancel(self, job_id: str) -> Job:
        job = await self.jobs.get(job_id)
        if job.status is JobStatus.RUNNING:
            raise InvalidStateTransitionError("a running task must cooperate with cancellation")
        if job.status.is_terminal:
            raise InvalidStateTransitionError(f"cannot cancel a {job.status} job")
        job.status = JobStatus.CANCELLED
        job.message = "cancelled before execution"
        job.refresh()
        return await self.jobs.update(job)

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
        job.message = "running"
        job.refresh()
        await self.jobs.update(job)

        async def update_progress(value: float, message: str | None) -> None:
            job.progress = value
            job.message = message
            job.refresh()
            await self.jobs.update(job)

        try:
            result = await self.tasks.call(
                job.request.task, TaskContext(job, update_progress), job.request.payload
            )
            job.artifacts = [await self._store_artifact(job, item) for item in result.files]
            job.output = result.output
            job.progress = 1.0
            job.status = JobStatus.SUCCEEDED
            job.message = "completed"
            job.refresh()
        except Exception as error:
            job.error = f"{type(error).__name__}: {error}"
            if job.attempt < job.request.max_attempts:
                job.status = JobStatus.QUEUED
                job.message = "retrying"
                job.refresh()
                await self.jobs.update(job)
                await self.queue.enqueue(job.id)
                return job
            job.status = JobStatus.FAILED
            job.message = "failed"
            job.refresh()
        return await self.jobs.update(job)

    async def _store_artifact(self, job: Job, item: ArtifactInput):
        source = Path(item.path)
        return await self.artifacts.put_file(
            source,
            name=item.name or source.name,
            kind=item.kind,
            media_type=item.media_type,
            expires_at=job.artifact_expiry(),
        )
