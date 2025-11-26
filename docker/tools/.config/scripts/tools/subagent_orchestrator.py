#!/usr/bin/env python3
"""
Subagent Orchestrator - High-performance parallel task execution.

This module re-exports all functionality from the orchestrator package.
For the full implementation, see the orchestrator/ subpackage.

Config-first design using .config/copilot/orchestration/subagent-config.yml
for propagating settings throughout the codebase.

Reference: docs/retro/workforce/subagent-capabilities.md

RTX Compute Integration:
- GPU-accelerated inference via ONNX Runtime CUDA/TensorRT
- Docker registry integration (localhost:5000)
- Parallel container execution with NVIDIA runtime
"""

from __future__ import annotations

# Try relative import first (when used as part of package)
# Fall back to direct import (when run standalone or from same directory)
try:
    from .orchestrator import (  # type: ignore[import-not-found]
        GPU_CONFIG,
        PRECOMPILED_IMAGES,
        REGISTRY_URL,
        DockerExecutor,
        DownsertExecutor,
        GPUInferenceExecutor,
        ParallelSearchExecutor,
        RegistrySyncExecutor,
        SubagentConfig,
        SubagentOrchestrator,
        SubagentTask,
        TaskExecutor,
        TaskResult,
        TaskStatus,
        TaskType,
        UpsertExecutor,
        ValidationExecutor,
        XMLTemplateRenderer,
        batch_downsert,
        batch_upsert,
        create_full_orchestrator,
        parallel_search,
        parallel_validation,
        run_docker_task,
        run_gpu_inference,
        sync_registry,
    )
    from .orchestrator.cli import main  # type: ignore[import-not-found]
except ImportError:
    from orchestrator import (  # type: ignore[import-not-found]
        GPU_CONFIG,
        PRECOMPILED_IMAGES,
        REGISTRY_URL,
        DockerExecutor,
        DownsertExecutor,
        GPUInferenceExecutor,
        ParallelSearchExecutor,
        RegistrySyncExecutor,
        SubagentConfig,
        SubagentOrchestrator,
        SubagentTask,
        TaskExecutor,
        TaskResult,
        TaskStatus,
        TaskType,
        UpsertExecutor,
        ValidationExecutor,
        XMLTemplateRenderer,
        batch_downsert,
        batch_upsert,
        create_full_orchestrator,
        parallel_search,
        parallel_validation,
        run_docker_task,
        run_gpu_inference,
        sync_registry,
    )
    from orchestrator.cli import main  # type: ignore[import-not-found]

__all__ = [
    "GPU_CONFIG",
    "PRECOMPILED_IMAGES",
    "REGISTRY_URL",
    "DockerExecutor",
    "DownsertExecutor",
    "GPUInferenceExecutor",
    "ParallelSearchExecutor",
    "RegistrySyncExecutor",
    "SubagentConfig",
    "SubagentOrchestrator",
    "SubagentTask",
    "TaskExecutor",
    "TaskResult",
    "TaskStatus",
    "TaskType",
    "UpsertExecutor",
    "ValidationExecutor",
    "XMLTemplateRenderer",
    "batch_downsert",
    "batch_upsert",
    "create_full_orchestrator",
    "main",
    "parallel_search",
    "parallel_validation",
    "run_docker_task",
    "run_gpu_inference",
    "sync_registry",
]

if __name__ == "__main__":
    main()
