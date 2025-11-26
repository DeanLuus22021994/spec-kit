"""File operations executors (upsert/downsert)."""

from __future__ import annotations

import concurrent.futures
import json
import shutil
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from ..config import SubagentConfig, SubagentTask, TaskResult, TaskStatus
from .base import TaskExecutor

ThreadPoolExecutor = concurrent.futures.ThreadPoolExecutor
as_completed = concurrent.futures.as_completed


class UpsertExecutor(TaskExecutor):
    """Executor for upsert (create-or-update) operations."""

    def __init__(
        self, upsert_func: Callable[[str, Any], dict[str, Any]] | None = None
    ) -> None:
        """Initialize with optional custom upsert function."""
        self.upsert_func = upsert_func
        self.config = SubagentConfig.load()
        perf = self.config.get("performance_targets", {})
        self.max_workers: int = perf.get("max_parallel_agents", 8) if perf else 8

    def _default_upsert(self, target: str, data: Any) -> dict[str, Any]:
        """Default upsert: write file or create resource."""
        target_path = Path(target)
        existed = target_path.exists()

        if isinstance(data, dict):
            content = json.dumps(data, indent=2)
        elif isinstance(data, str):
            content = data
        else:
            content = str(data)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")

        return {
            "target": target,
            "action": "updated" if existed else "created",
            "size_bytes": len(content),
        }

    async def execute(self, task: SubagentTask) -> TaskResult:
        """Execute batch upsert operations."""
        start_time = time.perf_counter()
        payload = cast(dict[str, Any], task.payload)
        items: list[dict[str, Any]] = payload.get("items", [])
        results: list[dict[str, Any]] = []
        errors: list[str] = []

        upsert_fn = self.upsert_func or self._default_upsert

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(upsert_fn, item["target"], item["data"]): item
                for item in items
            }

            for future in as_completed(futures, timeout=task.timeout_seconds):
                item = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except (OSError, ValueError, RuntimeError) as e:
                    errors.append(f"Upsert '{item['target']}' failed: {e}")

        execution_time = (time.perf_counter() - start_time) * 1000

        return TaskResult(
            task_id=task.task_id,
            task_type=task.task_type,
            status=TaskStatus.COMPLETED if not errors else TaskStatus.FAILED,
            result={
                "items": results,
                "summary": {
                    "total": len(items),
                    "succeeded": len(results),
                    "created": sum(1 for r in results if r.get("action") == "created"),
                    "updated": sum(1 for r in results if r.get("action") == "updated"),
                },
            },
            error="; ".join(errors) if errors else None,
            execution_time_ms=execution_time,
            parallel_calls=len(items),
        )

    def validate_task(self, task: SubagentTask) -> bool:
        """Validate upsert task."""
        payload = task.payload
        if not isinstance(payload, dict) or "items" not in payload:
            return False
        items = payload["items"]
        return isinstance(items, list) and all(
            isinstance(item, dict) and "target" in item and "data" in item
            for item in items
        )


class DownsertExecutor(TaskExecutor):
    """Executor for downsert (delete-if-exists) operations."""

    def __init__(
        self, downsert_func: Callable[[str], dict[str, Any]] | None = None
    ) -> None:
        """Initialize with optional custom downsert function."""
        self.downsert_func = downsert_func
        self.config = SubagentConfig.load()
        perf = self.config.get("performance_targets", {})
        self.max_workers: int = perf.get("max_parallel_agents", 8) if perf else 8

    def _default_downsert(self, target: str) -> dict[str, Any]:
        """Default downsert: remove file or resource if exists."""
        target_path = Path(target)
        existed = target_path.exists()

        if existed:
            if target_path.is_dir():
                shutil.rmtree(target_path)
            else:
                target_path.unlink()

        return {
            "target": target,
            "action": "deleted" if existed else "skipped",
            "existed": existed,
        }

    async def execute(self, task: SubagentTask) -> TaskResult:
        """Execute batch downsert operations."""
        start_time = time.perf_counter()
        payload = cast(dict[str, Any], task.payload)
        targets: list[str] = payload.get("targets", [])
        results: list[dict[str, Any]] = []
        errors: list[str] = []

        downsert_fn = self.downsert_func or self._default_downsert

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(downsert_fn, target): target for target in targets
            }

            for future in as_completed(futures, timeout=task.timeout_seconds):
                target = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except (OSError, ValueError, RuntimeError) as e:
                    errors.append(f"Downsert '{target}' failed: {e}")

        execution_time = (time.perf_counter() - start_time) * 1000

        return TaskResult(
            task_id=task.task_id,
            task_type=task.task_type,
            status=TaskStatus.COMPLETED if not errors else TaskStatus.FAILED,
            result={
                "items": results,
                "summary": {
                    "total": len(targets),
                    "succeeded": len(results),
                    "deleted": sum(1 for r in results if r.get("action") == "deleted"),
                    "skipped": sum(1 for r in results if r.get("action") == "skipped"),
                },
            },
            error="; ".join(errors) if errors else None,
            execution_time_ms=execution_time,
            parallel_calls=len(targets),
        )

    def validate_task(self, task: SubagentTask) -> bool:
        """Validate downsert task."""
        payload = task.payload
        if not isinstance(payload, dict) or "targets" not in payload:
            return False
        targets = payload["targets"]
        return isinstance(targets, list) and all(isinstance(t, str) for t in targets)
