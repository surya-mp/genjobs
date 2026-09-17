"""Exceptions raised by GenJobs."""


class GenJobsError(Exception):
    """Base exception for the package."""


class JobNotFoundError(GenJobsError):
    """Raised when a job identifier is unknown to the configured job store."""


class TaskNotFoundError(GenJobsError):
    """Raised when a queued job has no registered task handler."""


class InvalidStateTransitionError(GenJobsError):
    """Raised when an operation conflicts with the current job state."""
