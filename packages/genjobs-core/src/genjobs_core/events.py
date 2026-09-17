"""Vendor-neutral lifecycle events for logging, metrics, and tracing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from .models import JobStatus


@dataclass(frozen=True, slots=True)
class JobEvent:
    name: str
    job_id: str
    task: str
    status: JobStatus
    attempt: int
    occurred_at: datetime
    progress: float
    message: str | None


class JobObserver(Protocol):
    """Receives lifecycle events; observer failures never fail a job."""

    async def on_event(self, event: JobEvent) -> None: ...
