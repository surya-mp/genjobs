"""Public API for the dependency-free GenJobs core package."""

from .engine import GenJobs
from .errors import GenJobsError, InvalidStateTransitionError, JobNotFoundError, TaskNotFoundError
from .events import JobEvent, JobObserver
from .models import (
    Artifact,
    ArtifactInput,
    ContentKind,
    InputAsset,
    Job,
    JobRequest,
    JobStatus,
    RetryPolicy,
    TaskResult,
)
from .tasks import TaskContext

__all__ = [
    "Artifact",
    "ArtifactInput",
    "ContentKind",
    "GenJobs",
    "GenJobsError",
    "InputAsset",
    "InvalidStateTransitionError",
    "Job",
    "JobEvent",
    "JobNotFoundError",
    "JobObserver",
    "JobRequest",
    "JobStatus",
    "RetryPolicy",
    "TaskContext",
    "TaskNotFoundError",
    "TaskResult",
]
