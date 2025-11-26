"""Search and validation executors."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from ..config import SubagentTask
from .parallel import ParallelExecutor


class ParallelSearchExecutor(ParallelExecutor[str, "list[dict[str, Any]]"]):
    """Executor for parallel file/grep searches."""

    def __init__(self, search_func: Callable[[str], list[dict[str, Any]]]) -> None:
        """Initialize with search function."""
        super().__init__()
        self.search_func = search_func

    def get_items(self, task: SubagentTask) -> list[str]:
        """Get search patterns from task."""
        return cast(list[str], task.payload)

    def process_item(self, item: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Execute search for a single pattern."""
        return self.search_func(item)

    def aggregate_results(
        self, results: list[list[dict[str, Any]]]
    ) -> list[dict[str, Any]]:
        """Flatten search results."""
        flat_results = []
        for r in results:
            flat_results.extend(r)
        return flat_results

    def validate_task(self, task: SubagentTask) -> bool:
        """Validate search patterns."""
        payload = task.payload
        return (
            bool(payload)
            and isinstance(payload, list)
            and all(isinstance(p, str) for p in payload)
        )


class ValidationExecutor(ParallelExecutor[str, "tuple[str, dict[str, Any]]"]):
    """Executor for validation tasks."""

    def __init__(self, validator_func: Callable[[str, str], dict[str, Any]]) -> None:
        """Initialize with validation function."""
        super().__init__()
        self.validator_func = validator_func

    def get_items(self, task: SubagentTask) -> list[str]:
        """Get files to validate from task."""
        payload = cast(dict[str, Any], task.payload)
        return cast(list[str], payload.get("files", []))

    def process_item(self, item: str, **kwargs: Any) -> tuple[str, dict[str, Any]]:
        """Validate a single file."""
        task = cast(SubagentTask, kwargs.get("task"))
        payload = cast(dict[str, Any], task.payload)
        profile = payload.get("profile", "development")
        return item, self.validator_func(item, profile)

    def aggregate_results(
        self, results: list[tuple[str, dict[str, Any]]]
    ) -> dict[str, Any]:
        """Aggregate validation results."""
        file_results = {path: res for path, res in results}

        # Aggregate summary
        total_errors = sum(len(r.get("errors", [])) for r in file_results.values())
        total_warnings = sum(len(r.get("warnings", [])) for r in file_results.values())

        return {
            "files": file_results,
            "summary": {
                "total_files": len(results),
                "validated": len(file_results),
                "errors": total_errors,
                "warnings": total_warnings,
                "passed": not total_errors,
            },
        }

    def validate_task(self, task: SubagentTask) -> bool:
        """Validate task structure."""
        payload = task.payload
        return (
            isinstance(payload, dict)
            and "files" in payload
            and isinstance(payload["files"], list)
        )
