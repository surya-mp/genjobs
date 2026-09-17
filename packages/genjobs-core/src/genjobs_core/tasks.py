"""Task registration and execution context."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable

from .models import Job, TaskResult, utcnow

TaskHandler = Callable[["TaskContext", dict[str, object]], TaskResult | Awaitable[TaskResult]]


class TaskContext:
    """Capabilities available to a task without coupling it to a backend."""

    def __init__(
        self,
        job: Job,
        update_progress: Callable[[float, str | None], Awaitable[None]],
        is_cancel_requested: Callable[[], Awaitable[bool]],
    ):
        self.job = job
        self._update_progress = update_progress
        self._is_cancel_requested = is_cancel_requested

    async def progress(self, value: float, message: str | None = None) -> None:
        """Persist progress between 0 and 1 for clients polling a job."""
        if not 0 <= value <= 1:
            raise ValueError("progress must be between 0 and 1")
        await self._update_progress(value, message)

    async def heartbeat(self, message: str | None = None) -> None:
        """Record liveness for monitoring and lease-aware backend implementations."""
        self.job.heartbeat_at = utcnow()
        await self._update_progress(self.job.progress, message or self.job.message)

    async def cancel_requested(self) -> bool:
        """Allow cooperative task code to stop model work cleanly."""
        return await self._is_cancel_requested()


class TaskRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, TaskHandler] = {}

    def register(self, name: str) -> Callable[[TaskHandler], TaskHandler]:
        if not name.strip():
            raise ValueError("task name must not be blank")

        def decorator(handler: TaskHandler) -> TaskHandler:
            if name in self._handlers:
                raise ValueError(f"task already registered: {name}")
            self._handlers[name] = handler
            return handler

        return decorator

    def get(self, name: str) -> TaskHandler | None:
        return self._handlers.get(name)

    async def call(self, name: str, context: TaskContext, payload: dict[str, object]) -> TaskResult:
        handler = self._handlers[name]
        result = handler(context, payload)
        if inspect.isawaitable(result):
            result = await result
        return result
