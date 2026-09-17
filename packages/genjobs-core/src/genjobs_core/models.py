"""Provider-neutral domain objects for asynchronous work."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import uuid4


def utcnow() -> datetime:
    return datetime.now(UTC)


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        return self in {self.SUCCEEDED, self.FAILED, self.CANCELLED}


class ContentKind(StrEnum):
    """A coarse, portable description of an input or output value.

    This is metadata only. GenJobs does not validate a model's prompt, media
    dimensions, codec, tokenizer, or provider-specific request schema.
    """

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    FILE = "file"
    STRUCTURED = "structured"


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Retry timing controls interpreted by queues that support delayed delivery."""

    initial_delay_seconds: float = 0.0
    multiplier: float = 2.0
    max_delay_seconds: float = 300.0

    def __post_init__(self) -> None:
        if self.initial_delay_seconds < 0:
            raise ValueError("initial_delay_seconds must not be negative")
        if self.multiplier < 1:
            raise ValueError("multiplier must be at least 1")
        if self.max_delay_seconds < self.initial_delay_seconds:
            raise ValueError("max_delay_seconds must be at least initial_delay_seconds")

    def delay_for_attempt(self, failed_attempt: int) -> float:
        """Return exponential backoff for a failed one-based attempt number."""
        if failed_attempt < 1:
            raise ValueError("failed_attempt must be at least 1")
        return min(
            self.initial_delay_seconds * self.multiplier ** (failed_attempt - 1),
            self.max_delay_seconds,
        )


@dataclass(frozen=True, slots=True)
class InputAsset:
    """A task input referenced by a path, URI, object key, or opaque handle."""

    location: str
    kind: ContentKind = ContentKind.FILE
    media_type: str | None = None
    metadata: dict[str, object] = field(default_factory=dict[str, object])

    def __post_init__(self) -> None:
        if not self.location.strip():
            raise ValueError("input asset location must not be blank")


@dataclass(frozen=True, slots=True)
class JobRequest:
    """An infrastructure-neutral request to execute a named task."""

    task: str
    payload: dict[str, object] = field(default_factory=dict[str, object])
    inputs: tuple[InputAsset, ...] = ()
    idempotency_key: str | None = None
    max_attempts: int = 1
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    artifact_ttl_seconds: int = 3600

    def __post_init__(self) -> None:
        if not self.task.strip():
            raise ValueError("task must not be blank")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.artifact_ttl_seconds < 1:
            raise ValueError("artifact_ttl_seconds must be at least 1")


@dataclass(frozen=True, slots=True)
class ArtifactInput:
    """A file created by a task before it is handed to an artifact store."""

    path: str
    name: str | None = None
    kind: ContentKind = ContentKind.FILE
    media_type: str | None = None


@dataclass(frozen=True, slots=True)
class Artifact:
    """A temporary result reference. `location` is backend-specific."""

    id: str
    name: str
    location: str
    expires_at: datetime
    kind: ContentKind = ContentKind.FILE
    media_type: str | None = None

    @property
    def is_expired(self) -> bool:
        return self.expires_at <= utcnow()


@dataclass(frozen=True, slots=True)
class TaskResult:
    """The result a task handler returns to the GenJobs worker."""

    output: dict[str, object] = field(default_factory=dict[str, object])
    files: list[ArtifactInput] = field(default_factory=list[ArtifactInput])


@dataclass(slots=True)
class Job:
    """The durable state of one task execution."""

    id: str
    request: JobRequest
    status: JobStatus = JobStatus.QUEUED
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    attempt: int = 0
    progress: float = 0.0
    retry_at: datetime | None = None
    heartbeat_at: datetime | None = None
    cancel_requested: bool = False
    message: str | None = None
    output: dict[str, object] | None = None
    artifacts: list[Artifact] = field(default_factory=list[Artifact])
    error: str | None = None

    @classmethod
    def from_request(cls, request: JobRequest) -> Job:
        return cls(id=str(uuid4()), request=request)

    def refresh(self) -> None:
        self.updated_at = utcnow()

    def artifact_expiry(self) -> datetime:
        return utcnow() + timedelta(seconds=self.request.artifact_ttl_seconds)
