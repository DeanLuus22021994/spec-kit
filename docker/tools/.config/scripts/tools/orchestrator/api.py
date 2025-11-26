"""High-level API functions for the subagent orchestrator."""

from __future__ import annotations

from typing import Any, Callable, cast

from .config import GPU_CONFIG, PRECOMPILED_IMAGES, SubagentTask, TaskType
from .executors.docker import DockerExecutor, GPUInferenceExecutor, RegistrySyncExecutor
from .executors.file_ops import DownsertExecutor, UpsertExecutor
from .executors.search import ParallelSearchExecutor, ValidationExecutor
from .orchestrator import SubagentOrchestrator


async def parallel_search(
    patterns: list[str], search_func: Callable[[str], list[dict[str, Any]]]
) -> list[dict[str, Any]]:
    """Execute parallel searches."""
    orchestrator = SubagentOrchestrator()
    executor = ParallelSearchExecutor(search_func)
    orchestrator.register_executor(TaskType.PARALLEL_GREP, executor)

    task = SubagentTask(
        task_id="parallel-search-001",
        task_type=TaskType.PARALLEL_GREP,
        payload=patterns,
    )

    results = await orchestrator.execute_batch([task])
    if results and results[0].result:
        return cast(list[dict[str, Any]], results[0].result)
    return []


async def parallel_validation(
    files: list[str],
    profile: str,
    validator_func: Callable[[str, str], dict[str, Any]],
) -> dict[str, Any]:
    """Execute parallel validation."""
    orchestrator = SubagentOrchestrator(profile=profile)
    executor = ValidationExecutor(validator_func)
    orchestrator.register_executor(TaskType.VALIDATION, executor)

    task = SubagentTask(
        task_id="validation-001",
        task_type=TaskType.VALIDATION,
        payload={"files": files, "profile": profile},
    )

    results = await orchestrator.execute_batch([task])
    if results and results[0].result:
        return cast(dict[str, Any], results[0].result)
    return {}


async def run_gpu_inference(
    model_type: str = "arcface",
    batch_size: int = 1,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """Run GPU inference using precompiled containers."""
    orchestrator = SubagentOrchestrator()
    executor = GPUInferenceExecutor()
    orchestrator.register_executor(TaskType.GPU_INFERENCE, executor)

    task = SubagentTask(
        task_id="gpu-inference-001",
        task_type=TaskType.GPU_INFERENCE,
        payload={"model_type": model_type, "batch_size": batch_size},
        timeout_seconds=timeout,
    )

    results = await orchestrator.execute_batch([task])
    if results and results[0].result:
        return cast(dict[str, Any], results[0].result)
    return {"error": results[0].error if results else "No results"}


async def batch_upsert(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Batch upsert (create-or-update) files/resources."""
    orchestrator = SubagentOrchestrator()
    executor = UpsertExecutor()
    orchestrator.register_executor(TaskType.UPSERT, executor)

    task = SubagentTask(
        task_id="upsert-batch-001",
        task_type=TaskType.UPSERT,
        payload={"items": items},
    )

    results = await orchestrator.execute_batch([task])
    if results and results[0].result:
        return cast(dict[str, Any], results[0].result)
    return {"error": results[0].error if results else "No results"}


async def batch_downsert(targets: list[str]) -> dict[str, Any]:
    """Batch downsert (delete-if-exists) files/resources."""
    orchestrator = SubagentOrchestrator()
    executor = DownsertExecutor()
    orchestrator.register_executor(TaskType.DOWNSERT, executor)

    task = SubagentTask(
        task_id="downsert-batch-001",
        task_type=TaskType.DOWNSERT,
        payload={"targets": targets},
    )

    results = await orchestrator.execute_batch([task])
    if results and results[0].result:
        return cast(dict[str, Any], results[0].result)
    return {"error": results[0].error if results else "No results"}


async def sync_registry(
    action: str = "list", images: list[str] | None = None
) -> dict[str, Any]:
    """Sync with Docker registry."""
    orchestrator = SubagentOrchestrator()
    executor = RegistrySyncExecutor()
    orchestrator.register_executor(TaskType.REGISTRY_SYNC, executor)

    task = SubagentTask(
        task_id="registry-sync-001",
        task_type=TaskType.REGISTRY_SYNC,
        payload={"action": action, "images": images or []},
    )

    results = await orchestrator.execute_batch([task])
    if results and results[0].result:
        return cast(dict[str, Any], results[0].result)
    return {"error": results[0].error if results else "No results"}


async def run_docker_task(
    image: str,
    command: list[str],
    gpu: bool = False,
    volumes: dict[str, str] | None = None,
    env: dict[str, str] | None = None,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """Run a Docker container task."""
    orchestrator = SubagentOrchestrator()
    executor = DockerExecutor()
    orchestrator.register_executor(TaskType.DOCKER_RUN, executor)

    task = SubagentTask(
        task_id="docker-run-001",
        task_type=TaskType.DOCKER_RUN,
        payload={
            "image": image,
            "command": command,
            "gpu": gpu,
            "volumes": volumes or {},
            "env": env or {},
        },
        timeout_seconds=timeout,
    )

    results = await orchestrator.execute_batch([task])
    if results and results[0].result:
        return cast(dict[str, Any], results[0].result)
    return {"error": results[0].error if results else "No results"}


def create_full_orchestrator() -> SubagentOrchestrator:
    """Create an orchestrator with all executors registered."""
    orchestrator = SubagentOrchestrator()

    orchestrator.register_executor(TaskType.DOCKER_RUN, DockerExecutor())
    orchestrator.register_executor(TaskType.GPU_INFERENCE, GPUInferenceExecutor())
    orchestrator.register_executor(TaskType.UPSERT, UpsertExecutor())
    orchestrator.register_executor(TaskType.DOWNSERT, DownsertExecutor())
    orchestrator.register_executor(TaskType.REGISTRY_SYNC, RegistrySyncExecutor())

    return orchestrator


# Re-export config constants for convenience
__all__ = [
    "GPU_CONFIG",
    "PRECOMPILED_IMAGES",
    "batch_downsert",
    "batch_upsert",
    "create_full_orchestrator",
    "parallel_search",
    "parallel_validation",
    "run_docker_task",
    "run_gpu_inference",
    "sync_registry",
]
