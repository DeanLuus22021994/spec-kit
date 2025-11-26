"""Search and validation executors."""

from __future__ import annotations

import concurrent.futures
import time
from collections.abc import Callable
from typing import Any, cast

from ..config import SubagentConfig, SubagentTask, TaskResult, TaskStatus
from .base import TaskExecutor

ThreadPoolExecutor = concurrent.futures.ThreadPoolExecutor
as_completed = concurrent.futures.as_completed


class ParallelSearchExecutor(TaskExecutor):
    """Executor for parallel file/grep searches."""

    def __init__(self, search_func: Callable[[str], list[dict[str, Any]]]) -> None:
        """Initialize with search function."""
        self.search_func = search_func
        self.config = SubagentConfig.load()
        perf = self.config.get("performance_targets", {})
        self.max_workers: int = perf.get("max_parallel_agents", 8) if perf else 8

    async def execute(self, task: SubagentTask) -> TaskResult:
        """Execute parallel searches."""
        start_time = time.perf_counter()
        results: list[dict[str, Any]] = []
        errors: list[str] = []
        patterns = cast(list[str], task.payload)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.search_func, pattern): pattern
                for pattern in patterns
            }

            for future in as_completed(futures, timeout=task.timeout_seconds):
                pattern = futures[future]
                try:
                    result = future.result()
                    results.extend(result)
                except (OSError, ValueError, RuntimeError) as e:
                    errors.append(f"Search '{pattern}' failed: {e}")

        execution_time = (time.perf_counter() - start_time) * 1000

        return TaskResult(
            task_id=task.task_id,
            task_type=task.task_type,
            status=TaskStatus.COMPLETED if not errors else TaskStatus.FAILED,
            result=results,
            error="; ".join(errors) if errors else None,
            execution_time_ms=execution_time,
            parallel_calls=len(patterns),
        )

    def validate_task(self, task: SubagentTask) -> bool:
        """Validate search patterns."""
        payload = task.payload
        return (
            bool(payload)
            and isinstance(payload, list)
            and all(isinstance(p, str) for p in payload)
        )


class ValidationExecutor(TaskExecutor):
    """Executor for validation tasks."""

    def __init__(self, validator_func: Callable[[str, str], dict[str, Any]]) -> None:
        """Initialize with validation function."""
        self.validator_func = validator_func
        self.config = SubagentConfig.load()

    async def execute(self, task: SubagentTask) -> TaskResult:
        """Execute validation task."""
        start_time = time.perf_counter()
        payload = cast(dict[str, Any], task.payload)
        files: list[str] = payload.get("files", [])
        profile: str = payload.get("profile", "development")
        results: dict[str, Any] = {"files": {}, "summary": {}}
        errors: list[str] = []
        perf = self.config.get("performance_targets", {})
        max_workers: int = perf.get("max_parallel_agents", 8) if perf else 8

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.validator_func, f, profile): f for f in files
            }

            for future in as_completed(futures, timeout=task.timeout_seconds):
                file_path = futures[future]
                try:
                    result = future.result()
                    results["files"][file_path] = result
                except (OSError, ValueError, RuntimeError) as e:
                    errors.append(f"Validation '{file_path}' failed: {e}")

        # Aggregate summary
        total_errors = sum(len(r.get("errors", [])) for r in results["files"].values())
        total_warnings = sum(
            len(r.get("warnings", [])) for r in results["files"].values()
        )
        results["summary"] = {
            "total_files": len(files),
            "validated": len(results["files"]),
            "errors": total_errors,
            "warnings": total_warnings,
            "passed": not total_errors,
        }

        execution_time = (time.perf_counter() - start_time) * 1000

        return TaskResult(
            task_id=task.task_id,
            task_type=task.task_type,
            status=TaskStatus.COMPLETED if not errors else TaskStatus.FAILED,
            result=results,
            error="; ".join(errors) if errors else None,
            execution_time_ms=execution_time,
            parallel_calls=len(files),
        )

    def validate_task(self, task: SubagentTask) -> bool:
        """Validate task structure."""
        payload = task.payload
        return (
            isinstance(payload, dict)
            and "files" in payload
            and isinstance(payload["files"], list)
        )
