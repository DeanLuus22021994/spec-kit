"""Main orchestrator and template renderer."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from .config import SubagentConfig, SubagentTask, TaskResult, TaskStatus, TaskType
from .executors.base import TaskExecutor

logger = logging.getLogger(__name__)


class ExecutionPatternManager:
    """Manage execution patterns from config."""

    def __init__(self) -> None:
        """Initialize with config."""
        self.config = SubagentConfig.load()
        self.patterns = self.config.get("execution_patterns", {})

    def get_pattern(self, name: str) -> dict[str, Any]:
        """Get a specific execution pattern."""
        pattern = self.patterns.get(name, {})
        if isinstance(pattern, dict):
            return pattern
        return {}

    def list_patterns(self) -> list[str]:
        """List available execution patterns."""
        return list(self.patterns.keys())


class SubagentOrchestrator:
    """Main orchestrator for parallel subagent task execution."""

    def __init__(self, profile: str = "development") -> None:
        """Initialize orchestrator with profile."""
        self.config = SubagentConfig.load()
        self.profile = profile
        profiles = self.config.get("profiles", {})
        self.profile_config: dict[str, Any] = (
            profiles.get(profile, {}) if profiles else {}
        )
        self.executors: dict[TaskType, TaskExecutor] = {}
        self.task_queue: asyncio.Queue[SubagentTask] = asyncio.Queue()
        self.results: dict[str, TaskResult] = {}

    def register_executor(self, task_type: TaskType, executor: TaskExecutor) -> None:
        """Register an executor for a task type."""
        self.executors[task_type] = executor

    async def submit(self, task: SubagentTask) -> str:
        """Submit a task for execution."""
        if task.task_type not in self.executors:
            msg = f"No executor registered for task type: {task.task_type}"
            logger.error(msg)
            raise ValueError(msg)

        executor = self.executors[task.task_type]
        if not executor.validate_task(task):
            msg = f"Invalid task payload for type: {task.task_type}"
            logger.error(msg)
            raise ValueError(msg)

        await self.task_queue.put(task)
        logger.debug("Task submitted: %s", task.task_id)
        return task.task_id

    async def execute_batch(self, tasks: list[SubagentTask]) -> list[TaskResult]:
        """Execute a batch of tasks in parallel."""
        max_parallel: int = self.profile_config.get("max_parallel_agents", 8)
        logger.info(
            "Executing batch of %d tasks (max_parallel=%d)", len(tasks), max_parallel
        )

        independent_tasks = [t for t in tasks if not t.dependencies]
        dependent_tasks = [t for t in tasks if t.dependencies]

        results: list[TaskResult] = []

        # Execute independent tasks in parallel batches (fixed)
        for i in range(0, len(independent_tasks), max_parallel):
            batch = independent_tasks[i:i + max_parallel]
            logger.debug("Processing batch of %d independent tasks", len(batch))
            batch_results = await asyncio.gather(
                *[self._execute_task(task) for task in batch],
                return_exceptions=True,
            )
            for j, batch_result in enumerate(batch_results):
                if isinstance(batch_result, BaseException):
                    logger.error(
                        "Task %s failed with exception: %s",
                        batch[j].task_id,
                        batch_result,
                    )
                    task_result = TaskResult(
                        task_id=batch[j].task_id,
                        task_type=batch[j].task_type,
                        status=TaskStatus.FAILED,
                        error=str(batch_result),
                    )
                else:
                    task_result = batch_result
                results.append(task_result)
                self.results[batch[j].task_id] = task_result

        # Execute dependent tasks
        for task in dependent_tasks:
            deps_satisfied = all(
                self.results.get(
                    dep_id, TaskResult("", TaskType.VALIDATION, TaskStatus.PENDING)
                ).status
                == TaskStatus.COMPLETED
                for dep_id in task.dependencies
            )
            if deps_satisfied:
                logger.debug("Dependencies satisfied for task %s", task.task_id)
                result = await self._execute_task(task)
                results.append(result)
                self.results[task.task_id] = result
            else:
                logger.warning("Dependencies not satisfied for task %s", task.task_id)
                failed_result = TaskResult(
                    task_id=task.task_id,
                    task_type=task.task_type,
                    status=TaskStatus.CANCELLED,
                    error="Dependencies not satisfied",
                )
                results.append(failed_result)

        return results

    async def _execute_task(self, task: SubagentTask) -> TaskResult:
        """Execute a single task."""
        executor = self.executors.get(task.task_type)
        if not executor:
            return TaskResult(
                task_id=task.task_id,
                task_type=task.task_type,
                status=TaskStatus.FAILED,
                error=f"No executor for task type: {task.task_type}",
            )

        try:
            logger.debug("Starting task %s", task.task_id)
            return await asyncio.wait_for(
                executor.execute(task), timeout=task.timeout_seconds
            )
        except TimeoutError:
            logger.error("Task %s timed out", task.task_id)
            return TaskResult(
                task_id=task.task_id,
                task_type=task.task_type,
                status=TaskStatus.TIMEOUT,
                error=f"Task timed out after {task.timeout_seconds}s",
            )
        except (OSError, ValueError, RuntimeError) as e:
            logger.error("Task %s failed: %s", task.task_id, e)
            return TaskResult(
                task_id=task.task_id,
                task_type=task.task_type,
                status=TaskStatus.FAILED,
                error=str(e),
            )

    def generate_report(self) -> dict[str, Any]:
        """Generate execution report."""
        completed = [
            r for r in self.results.values() if r.status == TaskStatus.COMPLETED
        ]
        failed = [r for r in self.results.values() if r.status == TaskStatus.FAILED]
        total_time = sum(r.execution_time_ms for r in self.results.values())
        total_parallel = sum(r.parallel_calls for r in self.results.values())

        return {
            "summary": {
                "total_tasks": len(self.results),
                "completed": len(completed),
                "failed": len(failed),
                "success_rate": (
                    len(completed) / len(self.results) if self.results else 0
                ),
                "total_execution_time_ms": total_time,
                "total_parallel_calls": total_parallel,
                "parallel_efficiency": (
                    total_parallel / len(self.results) if self.results else 0
                ),
            },
            "tasks": {
                task_id: {
                    "type": result.task_type.name,
                    "status": result.status.name,
                    "execution_time_ms": result.execution_time_ms,
                    "parallel_calls": result.parallel_calls,
                    "error": result.error,
                }
                for task_id, result in self.results.items()
            },
            "profile": self.profile,
            "config": {
                "max_parallel_agents": self.profile_config.get("max_parallel_agents"),
                "timeout_seconds": self.profile_config.get("timeout_seconds"),
            },
        }


class XMLTemplateRenderer:
    """Render XML prompt templates from config."""

    def __init__(self) -> None:
        """Initialize with config."""
        self.config = SubagentConfig.load()
        templates = self.config.get("xml_templates", {})
        self.templates: dict[str, str] = templates if templates else {}
        self._load_file_templates()

    def _load_file_templates(self) -> None:
        """Load templates from the virtual config directory."""
        # Try to locate the virtual config templates directory
        # Use configured path or fallback to default
        configured_path = self.config.get("paths.templates")
        if configured_path:
            template_dir = Path(configured_path)
        else:
            # Fallback to relative path
            template_dir = (
                Path(__file__).parents[5] / "src" / "virtual" / ".config" / "templates"
            )

        if template_dir.exists():
            for template_file in template_dir.glob("*.xml"):
                try:
                    name = template_file.stem
                    content = template_file.read_text(encoding="utf-8")
                    self.templates[name] = content
                except Exception as e:  # pylint: disable=broad-except
                    logger.warning("Failed to load template %s: %s", template_file, e)

    def render(self, template_name: str, **kwargs: Any) -> str:
        """Render a template with variables."""
        template = self.templates.get(template_name, "")
        if not template:
            msg = f"Template not found: {template_name}"
            raise ValueError(msg)

        result = str(template)
        for key, value in kwargs.items():
            placeholder = "{{" + key + "}}"
            result = result.replace(placeholder, str(value))

        return result

    def get_available_templates(self) -> list[str]:
        """Get list of available template names."""
        return list(self.templates.keys())
