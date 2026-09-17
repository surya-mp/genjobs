"""Public API for the dependency-free GenJobs core package."""

from .engine import GenJobs
from .errors import GenJobsError, InvalidStateTransitionError, JobNotFoundError, TaskNotFoundError
from .models import (
    Artifact,
    ArtifactInput,
    ContentKind,
    InputAsset,
    Job,
    JobRequest,
    JobStatus,
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
    "JobNotFoundError",
    "JobRequest",
    "JobStatus",
    "TaskContext",
    "TaskNotFoundError",
    "TaskResult",
]
