"""File operations executors (upsert/downsert)."""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from ..config import SubagentTask
from .parallel import ParallelExecutor


class UpsertExecutor(ParallelExecutor[dict[str, Any], dict[str, Any]]):
    """Executor for upsert (create-or-update) operations."""

    def __init__(
        self, upsert_func: Callable[[str, Any], dict[str, Any]] | None = None
    ) -> None:
        """Initialize with optional custom upsert function."""
        super().__init__()
        self.upsert_func = upsert_func

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

    def get_items(self, task: SubagentTask) -> list[dict[str, Any]]:
        """Get items to upsert from task."""
        payload = cast(dict[str, Any], task.payload)
        return cast(list[dict[str, Any]], payload.get("items", []))

    def process_item(self, item: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Upsert a single item."""
        upsert_fn = self.upsert_func or self._default_upsert
        return upsert_fn(item["target"], item["data"])

    def aggregate_results(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate upsert results."""
        return {
            "items": results,
            "summary": {
                "total": len(results),
                "succeeded": len(results),
                "created": sum(1 for r in results if r.get("action") == "created"),
                "updated": sum(1 for r in results if r.get("action") == "updated"),
            },
        }

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


class DownsertExecutor(ParallelExecutor[str, dict[str, Any]]):
    """Executor for downsert (delete-if-exists) operations."""

    def __init__(
        self, downsert_func: Callable[[str], dict[str, Any]] | None = None
    ) -> None:
        """Initialize with optional custom downsert function."""
        super().__init__()
        self.downsert_func = downsert_func

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

    def get_items(self, task: SubagentTask) -> list[str]:
        """Get targets to downsert from task."""
        payload = cast(dict[str, Any], task.payload)
        return cast(list[str], payload.get("targets", []))

    def process_item(self, item: str, **kwargs: Any) -> dict[str, Any]:
        """Downsert a single target."""
        downsert_fn = self.downsert_func or self._default_downsert
        return downsert_fn(item)

    def aggregate_results(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate downsert results."""
        return {
            "items": results,
            "summary": {
                "total": len(results),
                "succeeded": len(results),
                "deleted": sum(1 for r in results if r.get("action") == "deleted"),
                "skipped": sum(1 for r in results if r.get("action") == "skipped"),
            },
        }

    def validate_task(self, task: SubagentTask) -> bool:
        """Validate downsert task."""
        payload = task.payload
        if not isinstance(payload, dict) or "targets" not in payload:
            return False
        targets = payload["targets"]
        return isinstance(targets, list) and all(isinstance(t, str) for t in targets)
