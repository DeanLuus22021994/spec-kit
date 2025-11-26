"""Configuration and core types for the subagent orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any

import yaml

# =============================================================================
# REGISTRY CONFIGURATION - Precompiled Images
# =============================================================================
REGISTRY_URL = "localhost:5000"
PRECOMPILED_IMAGES = {
    "embeddings": f"{REGISTRY_URL}/semantic-kernel/embeddings:latest",
    "vector": f"{REGISTRY_URL}/semantic-kernel/vector:latest",
    "engine": f"{REGISTRY_URL}/semantic-kernel/engine:latest",
    "face-matcher": f"{REGISTRY_URL}/semantic-kernel/face-matcher:latest",
    "tools": "semantic-kernel-tools:precompiled",
}

# GPU Configuration for RTX 3050 (6GB VRAM)
GPU_CONFIG: dict[str, Any] = {
    "device_id": 0,
    "memory_fraction": 0.75,
    "cuda_visible_devices": "0",
    "nvidia_runtime": "nvidia",
    "tensorrt_enabled": True,
    "mixed_precision": True,
    "tf32_enabled": True,
    "flash_attention": True,
    "memory_pool_mb": 4096,
}


class TaskType(Enum):
    """Subagent task types aligned with config."""

    VALIDATION = auto()
    DIAGNOSTICS = auto()
    BATCH_EDIT = auto()
    RESEARCH = auto()
    FILE_SEARCH = auto()
    PARALLEL_GREP = auto()
    DOCKER_RUN = auto()
    UPSERT = auto()
    DOWNSERT = auto()
    GPU_INFERENCE = auto()
    REGISTRY_SYNC = auto()


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    TIMEOUT = auto()
    CANCELLED = auto()


@dataclass
class TaskResult:
    """Result container for subagent tasks."""

    task_id: str
    task_type: TaskType
    status: TaskStatus
    result: Any = None
    error: str | None = None
    execution_time_ms: float = 0.0
    parallel_calls: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SubagentTask:
    """Task definition for subagent execution."""

    task_id: str
    task_type: TaskType
    payload: Any
    timeout_seconds: float = 30.0
    max_retries: int = 3
    priority: int = 0
    dependencies: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Convert task_type string to Enum if necessary."""
        if isinstance(self.task_type, str):
            try:
                self.task_type = TaskType[self.task_type]
            except KeyError as e:
                msg = f"Invalid task type: {self.task_type}. Must be one of: {[t.name for t in TaskType]}"
                raise ValueError(msg) from e


class SubagentConfig:
    """Configuration loader for subagent orchestration."""

    _instance: SubagentConfig | None = None
    _config: dict[str, Any] = {}

    def __new__(cls) -> SubagentConfig:
        """Singleton pattern for config loading."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def load(cls, config_path: Path | None = None) -> dict[str, Any]:
        """Load configuration from YAML file."""
        if cls._config:
            return cls._config

        if config_path is None:
            config_path = (
                Path(__file__).parents[5]
                / ".config"
                / "copilot"
                / "orchestration"
                / "subagent-config.yml"
            )

        if not config_path.exists():
            cls._config = cls._get_defaults()
        else:
            with open(config_path, encoding="utf-8") as f:
                loaded_config = yaml.safe_load(f) or {}
                cls.validate(loaded_config)
                cls._config = loaded_config

        return cls._config

    @classmethod
    def validate(cls, config: dict[str, Any]) -> None:
        """Validate configuration structure."""
        required_keys = ["performance_targets"]
        for key in required_keys:
            if key not in config:
                msg = f"Missing required config key: {key}"
                raise ValueError(msg)

        perf = config.get("performance_targets", {})
        if not isinstance(perf, dict):
            msg = "performance_targets must be a dictionary"
            raise ValueError(msg)

        required_perf_keys = ["max_parallel_agents", "timeout_seconds"]
        for key in required_perf_keys:
            if key not in perf:
                msg = f"Missing required performance target: {key}"
                raise ValueError(msg)

    @classmethod
    def _get_defaults(cls) -> dict[str, Any]:
        """Default configuration if file not found."""
        return {
            "performance_targets": {
                "max_parallel_agents": 8,
                "target_utilization": 0.80,
                "safety_overhead": 0.05,
                "effective_utilization": 0.75,
                "timeout_seconds": 30,
                "retry_attempts": 3,
                "batch_size": 10,
            },
            "tracing": {"enabled": False},
            "metrics": {"enabled": False},
        }

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get configuration value by key path (dot notation)."""
        config = cls.load()
        keys = key.split(".")
        value: Any = config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value
