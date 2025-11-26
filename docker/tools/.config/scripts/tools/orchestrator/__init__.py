"""
Subagent Orchestrator Package - High-performance parallel task execution.

Config-first design using .config/copilot/orchestration/subagent-config.yml
for propagating settings throughout the codebase.

Reference: docs/retro/workforce/subagent-capabilities.md

RTX Compute Integration:
- GPU-accelerated inference via ONNX Runtime CUDA/TensorRT
- Docker registry integration (localhost:5000)
- Parallel container execution with NVIDIA runtime
"""

from __future__ import annotations

# High-level API functions (depends on all above)
from .api import (
    batch_downsert,
    batch_upsert,
    create_full_orchestrator,
    parallel_search,
    parallel_validation,
    run_docker_task,
    run_gpu_inference,
    sync_registry,
)

# Core types and config (must be first - no dependencies)
from .config import (
    GPU_CONFIG,
    PRECOMPILED_IMAGES,
    REGISTRY_URL,
    SubagentConfig,
    SubagentTask,
    TaskResult,
    TaskStatus,
    TaskType,
)

# Base executor (depends on config)
from .executors.base import TaskExecutor

# Concrete executors (depend on base and config)
from .executors.docker import DockerExecutor, GPUInferenceExecutor, RegistrySyncExecutor
from .executors.file_ops import DownsertExecutor, UpsertExecutor
from .executors.search import ParallelSearchExecutor, ValidationExecutor

# Main orchestrator (depends on executors and config)
from .orchestrator import SubagentOrchestrator, XMLTemplateRenderer

__all__ = [
    # Config & Types
    "GPU_CONFIG",
    "PRECOMPILED_IMAGES",
    "REGISTRY_URL",
    "SubagentConfig",
    "SubagentTask",
    "TaskExecutor",
    "TaskResult",
    "TaskStatus",
    "TaskType",
    # Executors
    "DockerExecutor",
    "DownsertExecutor",
    "GPUInferenceExecutor",
    "ParallelSearchExecutor",
    "RegistrySyncExecutor",
    "UpsertExecutor",
    "ValidationExecutor",
    # Orchestrator
    "SubagentOrchestrator",
    "XMLTemplateRenderer",
    # API Functions
    "batch_downsert",
    "batch_upsert",
    "create_full_orchestrator",
    "parallel_search",
    "parallel_validation",
    "run_docker_task",
    "run_gpu_inference",
    "sync_registry",
]
