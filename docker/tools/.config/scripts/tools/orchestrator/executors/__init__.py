"""Executor subpackage for task executors."""

from __future__ import annotations

from .base import TaskExecutor
from .docker import DockerExecutor, GPUInferenceExecutor, RegistrySyncExecutor
from .file_ops import DownsertExecutor, UpsertExecutor
from .search import ParallelSearchExecutor, ValidationExecutor

# Redis executors (optional - requires redis package)
try:
    from .redis_ops import (
        RedisClientPool,
        RedisConfig,
        RedisDataType,
        RedisDownsertExecutor,
        RedisUpsertExecutor,
        RedisUpsertItem,
        create_redis_executors,
    )

    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False
    RedisClientPool = None  # type: ignore[assignment,misc]
    RedisConfig = None  # type: ignore[assignment,misc]
    RedisDataType = None  # type: ignore[assignment,misc]
    RedisDownsertExecutor = None  # type: ignore[assignment,misc]
    RedisUpsertExecutor = None  # type: ignore[assignment,misc]
    RedisUpsertItem = None  # type: ignore[assignment,misc]
    create_redis_executors = None  # type: ignore[assignment]

__all__ = [
    # Base
    "TaskExecutor",
    # Docker
    "DockerExecutor",
    "GPUInferenceExecutor",
    "RegistrySyncExecutor",
    # File operations
    "DownsertExecutor",
    "UpsertExecutor",
    # Search
    "ParallelSearchExecutor",
    "ValidationExecutor",
    # Redis (optional)
    "RedisClientPool",
    "RedisConfig",
    "RedisDataType",
    "RedisDownsertExecutor",
    "RedisUpsertExecutor",
    "RedisUpsertItem",
    "create_redis_executors",
]
