"""Small contracts that cloud-specific packages can implement."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Protocol

from .models import Artifact, ContentKind, Job


class JobStore(Protocol):
    async def create(self, job: Job) -> Job: ...
    async def get(self, job_id: str) -> Job: ...
    async def update(self, job: Job) -> Job: ...
    async def find_by_idempotency_key(self, key: str) -> Job | None: ...


class JobQueue(Protocol):
    async def enqueue(self, job_id: str, *, delay_seconds: float = 0.0) -> None: ...
    async def dequeue(self) -> str | None: ...


class ArtifactStore(Protocol):
    async def put_file(
        self,
        source: Path,
        *,
        name: str,
        expires_at: datetime,
        kind: ContentKind = ContentKind.FILE,
        media_type: str | None = None,
    ) -> Artifact: ...

    async def delete(self, artifact: Artifact) -> None: ...
    async def delete_expired(self, *, now: datetime | None = None) -> int: ...
