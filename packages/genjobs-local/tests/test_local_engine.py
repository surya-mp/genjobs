import asyncio
from pathlib import Path

import pytest
from genjobs_core import (
    ArtifactInput,
    ContentKind,
    GenJobs,
    JobRequest,
    JobStatus,
    RetryPolicy,
    TaskContext,
    TaskResult,
)
from genjobs_local import InMemoryJobQueue, InMemoryJobStore, LocalArtifactStore


@pytest.mark.asyncio
async def test_runs_a_task_and_expires_artifacts_by_contract(tmp_path: Path) -> None:
    output = tmp_path / "model-output.mp4"
    output.write_bytes(b"not a real video")
    jobs = GenJobs(
        artifacts=LocalArtifactStore(tmp_path / "artifacts"),
        jobs=InMemoryJobStore(),
        queue=InMemoryJobQueue(),
    )

    @jobs.task("generate")
    async def generate(context: TaskContext, payload: dict[str, object]) -> TaskResult:
        await context.progress(0.5, "generating")
        return TaskResult(
            output={"provider": payload["provider"]},
            files=[
                ArtifactInput(
                    path=str(output),
                    kind=ContentKind.VIDEO,
                    media_type="video/mp4",
                )
            ],
        )

    submitted = await jobs.submit(
        JobRequest(
            task="generate",
            payload={"provider": "custom"},
            idempotency_key="same-request",
            artifact_ttl_seconds=60,
        )
    )
    assert (await jobs.submit(submitted.request)).id == submitted.id

    completed = await jobs.run_next()
    assert completed is not None
    assert completed.status is JobStatus.SUCCEEDED
    assert completed.progress == 1.0
    assert completed.output == {"provider": "custom"}
    assert len(completed.artifacts) == 1
    assert Path(completed.artifacts[0].location).is_file()
    assert completed.artifacts[0].kind is ContentKind.VIDEO
    assert not completed.artifacts[0].is_expired


@pytest.mark.asyncio
async def test_unknown_tasks_fail_without_crashing_the_worker(tmp_path: Path) -> None:
    jobs = GenJobs(
        artifacts=LocalArtifactStore(tmp_path / "artifacts"),
        jobs=InMemoryJobStore(),
        queue=InMemoryJobQueue(),
    )
    submitted = await jobs.submit(JobRequest(task="unregistered"))

    completed = await jobs.run_next()
    assert completed is not None
    assert completed.id == submitted.id
    assert completed.status is JobStatus.FAILED
    assert "unregistered" in (completed.error or "")


@pytest.mark.asyncio
async def test_retries_until_the_configured_attempt_limit(tmp_path: Path) -> None:
    jobs = GenJobs(
        artifacts=LocalArtifactStore(tmp_path / "artifacts"),
        jobs=InMemoryJobStore(),
        queue=InMemoryJobQueue(),
    )

    @jobs.task("flaky")
    async def flaky(context: TaskContext, payload: dict[str, object]) -> TaskResult:
        if context.job.attempt == 1:
            raise RuntimeError("temporary failure")
        return TaskResult(output={"retried": True})

    submitted = await jobs.submit(JobRequest(task="flaky", max_attempts=2))
    first_attempt = await jobs.run_next()
    assert first_attempt is not None
    assert first_attempt.status is JobStatus.QUEUED
    assert first_attempt.attempt == 1

    completed = await jobs.run_next()
    assert completed is not None
    assert completed.id == submitted.id
    assert completed.status is JobStatus.SUCCEEDED
    assert completed.attempt == 2


@pytest.mark.asyncio
async def test_retry_backoff_defers_a_second_attempt(tmp_path: Path) -> None:
    jobs = GenJobs(
        artifacts=LocalArtifactStore(tmp_path / "artifacts"),
        jobs=InMemoryJobStore(),
        queue=InMemoryJobQueue(),
    )

    @jobs.task("flaky")
    async def flaky(context: TaskContext, payload: dict[str, object]) -> TaskResult:
        if context.job.attempt == 1:
            raise RuntimeError("temporary failure")
        return TaskResult()

    await jobs.submit(
        JobRequest(
            task="flaky",
            max_attempts=2,
            retry_policy=RetryPolicy(initial_delay_seconds=0.01),
        )
    )
    assert (await jobs.run_next()).status is JobStatus.QUEUED
    assert await jobs.run_next() is None
    await asyncio.sleep(0.02)
    assert (await jobs.run_next()).status is JobStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_rejects_non_json_payloads(tmp_path: Path) -> None:
    jobs = GenJobs(
        artifacts=LocalArtifactStore(tmp_path / "artifacts"),
        jobs=InMemoryJobStore(),
        queue=InMemoryJobQueue(),
    )
    with pytest.raises(ValueError, match="JSON serializable"):
        await jobs.submit(JobRequest(task="test", payload={"invalid": object()}))
