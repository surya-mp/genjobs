"""Dependency-free local implementations for development and tests."""

from __future__ import annotations

import asyncio
import shutil
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from genjobs_core.errors import JobNotFoundError
from genjobs_core.models import Artifact, ContentKind, Job, utcnow


class InMemoryJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._idempotency: dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def create(self, job: Job) -> Job:
        async with self._lock:
            self._jobs[job.id] = job
            if job.request.idempotency_key:
                self._idempotency[job.request.idempotency_key] = job.id
            return job

    async def get(self, job_id: str) -> Job:
        async with self._lock:
            try:
                return self._jobs[job_id]
            except KeyError as error:
                raise JobNotFoundError(job_id) from error

    async def update(self, job: Job) -> Job:
        async with self._lock:
            if job.id not in self._jobs:
                raise JobNotFoundError(job.id)
            self._jobs[job.id] = job
            return job

    async def find_by_idempotency_key(self, key: str) -> Job | None:
        async with self._lock:
            job_id = self._idempotency.get(key)
            return self._jobs.get(job_id) if job_id else None


class InMemoryJobQueue:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[str] = asyncio.Queue()

    async def enqueue(self, job_id: str) -> None:
        await self._queue.put(job_id)

    async def dequeue(self) -> str | None:
        try:
            return self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return None


class LocalArtifactStore:
    """Copies temporary artifacts to disk. Appropriate only for local development."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self._artifacts: dict[str, Artifact] = {}

    async def put_file(
        self,
        source: Path,
        *,
        name: str,
        expires_at: datetime,
        kind: ContentKind = ContentKind.FILE,
        media_type: str | None = None,
    ) -> Artifact:
        if not source.is_file():
            raise FileNotFoundError(source)
        artifact_id = str(uuid4())
        destination = self.directory / f"{artifact_id}-{Path(name).name}"
        shutil.copy2(source, destination)
        artifact = Artifact(
            id=artifact_id,
            name=Path(name).name,
            location=str(destination),
            expires_at=expires_at,
            kind=kind,
            media_type=media_type,
        )
        self._artifacts[artifact_id] = artifact
        return artifact

    async def delete(self, artifact: Artifact) -> None:
        Path(artifact.location).unlink(missing_ok=True)
        self._artifacts.pop(artifact.id, None)

    async def delete_expired(self, *, now: datetime | None = None) -> int:
        moment = now or utcnow()
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=UTC)
        expired = [
            artifact for artifact in self._artifacts.values() if artifact.expires_at <= moment
        ]
        for artifact in expired:
            await self.delete(artifact)
        removed = len(expired)
        return removed
