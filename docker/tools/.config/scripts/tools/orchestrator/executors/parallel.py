"""Parallel execution base class."""

from __future__ import annotations

import concurrent.futures
import time
from abc import abstractmethod
from typing import Any, Generic, TypeVar

from ..config import SubagentConfig, SubagentTask, TaskResult, TaskStatus
from .base import TaskExecutor

T = TypeVar("T")
R = TypeVar("R")

ThreadPoolExecutor = concurrent.futures.ThreadPoolExecutor
as_completed = concurrent.futures.as_completed


class ParallelExecutor(TaskExecutor, Generic[T, R]):
    """Base executor for parallel tasks."""

    def __init__(self) -> None:
        """Initialize with config."""
        self.config = SubagentConfig.load()
        perf = self.config.get("performance_targets", {})
        self.max_workers: int = perf.get("max_parallel_agents", 8) if perf else 8

    @abstractmethod
    def process_item(self, item: T, **kwargs: Any) -> R:
        """Process a single item."""

    @abstractmethod
    def get_items(self, task: SubagentTask) -> list[T]:
        """Extract items to process from task."""

    @abstractmethod
    def aggregate_results(self, results: list[R]) -> Any:
        """Aggregate individual results into final task result."""

    async def execute(self, task: SubagentTask) -> TaskResult:
        """Execute parallel tasks."""
        start_time = time.perf_counter()
        items = self.get_items(task)
        results: list[R] = []
        errors: list[str] = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(self.process_item, item, task=task): item
                for item in items
            }

            # Process results as they complete
            for future in as_completed(future_to_item, timeout=task.timeout_seconds):
                item = future_to_item[future]
                try:
                    result = future.result()
                    results.append(result)
                except (OSError, ValueError, RuntimeError) as e:
                    errors.append(f"Processing {item} failed: {e}")
                except Exception as e:  # pylint: disable=broad-except
                    errors.append(f"Unexpected error processing {item}: {e}")

        execution_time = (time.perf_counter() - start_time) * 1000
        final_result = self.aggregate_results(results)

        return TaskResult(
            task_id=task.task_id,
            task_type=task.task_type,
            status=TaskStatus.COMPLETED if not errors else TaskStatus.FAILED,
            result=final_result,
            error="; ".join(errors) if errors else None,
            execution_time_ms=execution_time,
            parallel_calls=len(items),
        )
