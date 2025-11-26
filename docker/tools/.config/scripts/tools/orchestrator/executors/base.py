"""Base executor abstract class."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..config import SubagentTask, TaskResult


class TaskExecutor(ABC):
    """Abstract base for task executors."""

    @abstractmethod
    async def execute(self, task: SubagentTask) -> TaskResult:
        """Execute a subagent task."""

    @abstractmethod
    def validate_task(self, task: SubagentTask) -> bool:
        """Validate task before execution."""
