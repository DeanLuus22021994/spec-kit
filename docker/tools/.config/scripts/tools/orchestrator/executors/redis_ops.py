"""Redis operations executors with full Redis feature utilization.

This module provides Redis-native upsert/downsert executors that take full
advantage of Redis capabilities:
- TTL/expiration for automatic cleanup
- Hash operations for structured data
- Pipelining for batch efficiency
- Atomic operations (SETNX, SETEX, etc.)
- Pub/Sub for real-time notifications
- Lua scripting for complex atomic operations
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, cast

import redis  # noqa: E501  # pylint: disable=import-error

from ..config import SubagentConfig, SubagentTask, TaskResult, TaskStatus
from .base import TaskExecutor


class RedisDataType(Enum):
    """Redis data type for storage."""

    STRING = auto()  # Simple key-value
    HASH = auto()  # Hash map (for structured objects)
    JSON = auto()  # JSON serialized string
    LIST = auto()  # Redis list
    SET = auto()  # Redis set
    SORTED_SET = auto()  # Redis sorted set (zset)


@dataclass
class RedisUpsertItem:
    """Configuration for a single Redis upsert operation."""

    key: str
    data: Any
    data_type: RedisDataType = RedisDataType.JSON
    ttl_seconds: int | None = None  # None = no expiration
    nx: bool = False  # Only set if not exists
    xx: bool = False  # Only set if exists
    publish_channel: str | None = None  # Publish notification on upsert


@dataclass
class RedisConfig:
    """Redis connection configuration."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None
    decode_responses: bool = True
    socket_timeout: float = 5.0
    connection_pool_size: int = 10

    @classmethod
    def from_env(cls) -> RedisConfig:
        """Load configuration from environment or defaults."""
        return cls(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            password=os.getenv("REDIS_PASSWORD"),
        )


class RedisClientPool:
    """Singleton Redis client pool."""

    _instance: RedisClientPool | None = None
    _client: redis.Redis | None = None
    _config: RedisConfig | None = None

    def __new__(cls) -> RedisClientPool:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_client(cls, config: RedisConfig | None = None) -> redis.Redis:
        """Get or create Redis client."""
        if cls._client is None or (config and config != cls._config):
            cfg = config or RedisConfig.from_env()
            cls._config = cfg
            pool = redis.ConnectionPool(
                host=cfg.host,
                port=cfg.port,
                db=cfg.db,
                password=cfg.password,
                decode_responses=cfg.decode_responses,
                socket_timeout=cfg.socket_timeout,
                max_connections=cfg.connection_pool_size,
            )
            cls._client = redis.Redis(connection_pool=pool)
        return cls._client

    @classmethod
    def close(cls) -> None:
        """Close the connection pool."""
        if cls._client:
            cls._client.close()
            cls._client = None


# Lua script for atomic upsert with metadata tracking
UPSERT_LUA_SCRIPT = """
local key = KEYS[1]
local value = ARGV[1]
local ttl = tonumber(ARGV[2])
local nx = ARGV[3] == "1"
local xx = ARGV[4] == "1"
local timestamp = ARGV[5]

local existed = redis.call('EXISTS', key) == 1

-- Check NX/XX conditions
if nx and existed then
    return {0, "skipped", "key_exists"}
end
if xx and not existed then
    return {0, "skipped", "key_not_exists"}
end

-- Set the value
if ttl and ttl > 0 then
    redis.call('SETEX', key, ttl, value)
else
    redis.call('SET', key, value)
end

-- Store metadata
local meta_key = key .. ":meta"
redis.call('HSET', meta_key,
    'last_modified', timestamp,
    'version', redis.call('INCR', key .. ':version'),
    'size_bytes', #value
)
if ttl and ttl > 0 then
    redis.call('EXPIRE', meta_key, ttl)
end

local action = existed and "updated" or "created"
return {1, action, "success"}
"""

# Lua script for atomic downsert with cleanup
DOWNSERT_LUA_SCRIPT = """
local key = KEYS[1]
local timestamp = ARGV[1]

local existed = redis.call('EXISTS', key) == 1

if existed then
    -- Get size before deletion for stats
    local value = redis.call('GET', key)
    local size = value and #value or 0

    -- Delete key and metadata
    redis.call('DEL', key)
    redis.call('DEL', key .. ':meta')
    redis.call('DEL', key .. ':version')

    return {1, "deleted", size}
else
    return {0, "skipped", 0}
end
"""


class RedisUpsertExecutor(TaskExecutor):
    """
    Redis-native upsert executor with full feature utilization.

    Features:
    - Pipelining for batch operations (10x+ faster)
    - TTL support for automatic expiration
    - Hash storage for structured data
    - Atomic operations via Lua scripts
    - Pub/Sub notifications on changes
    - Metadata tracking (version, timestamps)
    """

    def __init__(
        self,
        config: RedisConfig | None = None,
        default_ttl: int | None = None,
        enable_pubsub: bool = True,
        enable_metadata: bool = True,
    ) -> None:
        """Initialize Redis upsert executor."""
        self.redis = RedisClientPool.get_client(config)
        self.default_ttl = default_ttl
        self.enable_pubsub = enable_pubsub
        self.enable_metadata = enable_metadata
        self.orchestrator_config = SubagentConfig.load()

        # Register Lua scripts
        self._upsert_script = self.redis.register_script(UPSERT_LUA_SCRIPT)

    def _serialize_data(
        self, data: Any, data_type: RedisDataType
    ) -> str | dict[str, str]:
        """Serialize data based on type."""
        if data_type == RedisDataType.JSON:
            if isinstance(data, str):
                return data
            return json.dumps(data, default=str)
        if data_type == RedisDataType.HASH:
            if isinstance(data, dict):
                return {
                    str(k): json.dumps(v) if not isinstance(v, str) else v
                    for k, v in data.items()
                }
            raise ValueError("HASH type requires dict data")
        if data_type == RedisDataType.STRING:
            return str(data)
        return json.dumps(data, default=str)

    def _upsert_single(  # pylint: disable=too-many-locals
        self,
        key: str,
        data: Any,
        data_type: RedisDataType = RedisDataType.JSON,
        ttl: int | None = None,
        nx: bool = False,
        xx: bool = False,
        publish_channel: str | None = None,
    ) -> dict[str, Any]:
        """Execute single upsert with full Redis features."""
        start = time.perf_counter()
        effective_ttl = ttl if ttl is not None else self.default_ttl
        timestamp = time.time()

        try:
            if data_type == RedisDataType.HASH and isinstance(data, dict):
                # Use HSET for hash data
                existed = int(self.redis.exists(key)) > 0
                serialized = self._serialize_data(data, data_type)

                pipe = self.redis.pipeline()
                pipe.delete(key)  # Clear existing hash
                pipe.hset(key, mapping=cast(Any, serialized))
                if effective_ttl:
                    pipe.expire(key, effective_ttl)
                if self.enable_metadata:
                    meta_key = f"{key}:meta"
                    pipe.hset(
                        meta_key,
                        mapping={
                            "last_modified": str(timestamp),
                            "data_type": "hash",
                            "field_count": str(len(data)),
                        },
                    )
                    if effective_ttl:
                        pipe.expire(meta_key, effective_ttl)
                pipe.execute()

                action = "updated" if existed else "created"
                status = "success"
            else:
                # Use Lua script for atomic JSON/string upsert
                serialized = self._serialize_data(data, data_type)
                result = self._upsert_script(
                    keys=[key],
                    args=[
                        cast(str, serialized),
                        str(effective_ttl or 0),
                        "1" if nx else "0",
                        "1" if xx else "0",
                        str(timestamp),
                    ],
                )
                _, action, status = result

            # Publish notification if enabled
            if self.enable_pubsub and publish_channel:
                self.redis.publish(
                    publish_channel,
                    json.dumps(
                        {
                            "event": "upsert",
                            "key": key,
                            "action": action,
                            "timestamp": timestamp,
                        }
                    ),
                )

            elapsed = (time.perf_counter() - start) * 1000

            return {
                "target": key,
                "action": action,
                "status": status,
                "data_type": data_type.name,
                "ttl": effective_ttl,
                "size_bytes": len(str(serialized)),
                "execution_time_ms": elapsed,
            }

        except redis.RedisError as e:
            return {
                "target": key,
                "action": "failed",
                "status": "error",
                "error": str(e),
            }

    def _upsert_batch_pipelined(
        self, items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:  # pylint: disable=too-many-locals
        """Execute batch upsert using Redis pipeline for efficiency."""
        timestamp = time.time()
        results: list[dict[str, Any]] = []

        pipe = self.redis.pipeline()
        item_keys: list[str] = []

        # Check existing keys first
        for item in items:
            key = item["target"]
            item_keys.append(key)
            pipe.exists(key)

        existence = pipe.execute()

        # Build batch operations
        pipe = self.redis.pipeline()
        for i, item in enumerate(items):
            key = item["target"]
            data = item["data"]
            data_type = RedisDataType[item.get("data_type", "JSON").upper()]
            ttl = item.get("ttl", self.default_ttl)
            existed = existence[i] > 0

            if data_type == RedisDataType.HASH and isinstance(data, dict):
                serialized = self._serialize_data(data, data_type)
                pipe.delete(key)
                pipe.hset(key, mapping=cast(Any, serialized))
                if ttl:
                    pipe.expire(key, ttl)
            else:
                serialized = self._serialize_data(data, data_type)
                if ttl:
                    pipe.setex(key, ttl, cast(str, serialized))
                else:
                    pipe.set(key, cast(str, serialized))

            # Queue metadata
            if self.enable_metadata:
                meta_key = f"{key}:meta"
                pipe.hset(
                    meta_key,
                    mapping={
                        "last_modified": str(timestamp),
                        "data_type": data_type.name.lower(),
                    },
                )
                if ttl:
                    pipe.expire(meta_key, ttl)

            results.append(
                {
                    "target": key,
                    "action": "updated" if existed else "created",
                    "data_type": data_type.name,
                    "ttl": ttl,
                    "size_bytes": len(str(serialized)),
                }
            )

        # Execute all at once
        pipe.execute()

        return results

    async def execute(self, task: SubagentTask) -> TaskResult:
        """Execute batch upsert with pipelining."""
        start_time = time.perf_counter()
        payload = task.payload
        items: list[dict[str, Any]] = payload.get("items", [])
        use_pipeline = payload.get("pipeline", True)  # Default to pipelining

        if use_pipeline and len(items) > 1:
            results = self._upsert_batch_pipelined(items)
        else:
            results = [
                self._upsert_single(
                    key=item["target"],
                    data=item["data"],
                    data_type=RedisDataType[item.get("data_type", "JSON").upper()],
                    ttl=item.get("ttl", self.default_ttl),
                    nx=item.get("nx", False),
                    xx=item.get("xx", False),
                    publish_channel=item.get("publish_channel"),
                )
                for item in items
            ]

        execution_time = (time.perf_counter() - start_time) * 1000

        errors = [r for r in results if r.get("action") == "failed"]

        return TaskResult(
            task_id=task.task_id,
            task_type=task.task_type,
            status=TaskStatus.COMPLETED if not errors else TaskStatus.FAILED,
            result={
                "items": results,
                "summary": {
                    "total": len(items),
                    "succeeded": len(items) - len(errors),
                    "created": sum(1 for r in results if r.get("action") == "created"),
                    "updated": sum(1 for r in results if r.get("action") == "updated"),
                    "skipped": sum(1 for r in results if r.get("action") == "skipped"),
                    "failed": len(errors),
                    "pipeline_used": use_pipeline and len(items) > 1,
                },
            },
            error="; ".join(e.get("error", "") for e in errors) if errors else None,
            execution_time_ms=execution_time,
            parallel_calls=len(items),
            metadata={
                "redis_host": self.redis.connection_pool.connection_kwargs.get("host"),
                "default_ttl": self.default_ttl,
            },
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


class RedisDownsertExecutor(TaskExecutor):
    """
    Redis-native downsert executor with pattern matching and cleanup.

    Features:
    - Pattern-based deletion (SCAN + DEL)
    - Atomic deletion via Lua scripts
    - Metadata cleanup
    - Pub/Sub notifications
    - Statistics tracking
    """

    def __init__(
        self,
        config: RedisConfig | None = None,
        enable_pubsub: bool = True,
        enable_pattern_delete: bool = True,
    ) -> None:
        """Initialize Redis downsert executor."""
        self.redis = RedisClientPool.get_client(config)
        self.enable_pubsub = enable_pubsub
        self.enable_pattern_delete = enable_pattern_delete
        self.orchestrator_config = SubagentConfig.load()

        # Register Lua script
        self._downsert_script = self.redis.register_script(DOWNSERT_LUA_SCRIPT)

    def _downsert_single(
        self, key: str, publish_channel: str | None = None
    ) -> dict[str, Any]:
        """Delete single key with metadata cleanup."""
        start = time.perf_counter()
        timestamp = time.time()

        try:
            result = self._downsert_script(
                keys=[key],
                args=[str(timestamp)],
            )
            _, action, size = result

            # Publish notification if enabled
            if self.enable_pubsub and publish_channel and action == "deleted":
                self.redis.publish(
                    publish_channel,
                    json.dumps(
                        {
                            "event": "downsert",
                            "key": key,
                            "action": action,
                            "timestamp": timestamp,
                        }
                    ),
                )

            elapsed = (time.perf_counter() - start) * 1000

            return {
                "target": key,
                "action": action,
                "existed": action == "deleted",
                "bytes_freed": size,
                "execution_time_ms": elapsed,
            }

        except redis.RedisError as e:
            return {
                "target": key,
                "action": "failed",
                "existed": False,
                "error": str(e),
            }

    def _downsert_pattern(self, pattern: str) -> list[dict[str, Any]]:
        """Delete all keys matching pattern using SCAN."""
        results: list[dict[str, Any]] = []
        cursor = 0
        total_deleted = 0
        total_bytes = 0

        while True:
            cursor, keys = self.redis.scan(cursor, match=pattern, count=100)

            if keys:
                # Get sizes before deletion
                pipe = self.redis.pipeline()
                for key in keys:
                    pipe.strlen(key)
                sizes = pipe.execute()

                # Delete keys and metadata
                pipe = self.redis.pipeline()
                for key in keys:
                    pipe.delete(key)
                    pipe.delete(f"{key}:meta")
                    pipe.delete(f"{key}:version")
                pipe.execute()

                for key, size in zip(keys, sizes, strict=False):
                    results.append(
                        {
                            "target": key,
                            "action": "deleted",
                            "existed": True,
                            "bytes_freed": size or 0,
                        }
                    )
                    total_deleted += 1
                    total_bytes += size or 0

            if not cursor:
                break

        return results

    def _downsert_batch_pipelined(self, targets: list[str]) -> list[dict[str, Any]]:
        """Batch delete using pipeline."""
        results: list[dict[str, Any]] = []

        # Check existence and get sizes
        pipe = self.redis.pipeline()
        for key in targets:
            pipe.exists(key)
            pipe.strlen(key)
        responses = pipe.execute()

        # Build deletion pipeline
        pipe = self.redis.pipeline()
        for i, key in enumerate(targets):
            existed = responses[i * 2] > 0
            size = responses[i * 2 + 1] or 0

            if existed:
                pipe.delete(key)
                pipe.delete(f"{key}:meta")
                pipe.delete(f"{key}:version")

            results.append(
                {
                    "target": key,
                    "action": "deleted" if existed else "skipped",
                    "existed": existed,
                    "bytes_freed": size if existed else 0,
                }
            )

        pipe.execute()

        return results

    async def execute(self, task: SubagentTask) -> TaskResult:
        """Execute batch downsert."""
        start_time = time.perf_counter()
        payload = task.payload
        targets: list[str] = payload.get("targets", [])
        pattern: str | None = payload.get("pattern")  # e.g., "test:*"
        use_pipeline = payload.get("pipeline", True)
        publish_channel = payload.get("publish_channel")

        results: list[dict[str, Any]] = []

        # Pattern-based deletion
        if pattern and self.enable_pattern_delete:
            results = self._downsert_pattern(pattern)
        # Batch deletion with pipeline
        elif use_pipeline and len(targets) > 1:
            results = self._downsert_batch_pipelined(targets)
        # Single key deletion
        else:
            results = [self._downsert_single(key, publish_channel) for key in targets]

        execution_time = (time.perf_counter() - start_time) * 1000

        errors = [r for r in results if r.get("action") == "failed"]
        total_bytes_freed = sum(r.get("bytes_freed", 0) for r in results)

        return TaskResult(
            task_id=task.task_id,
            task_type=task.task_type,
            status=TaskStatus.COMPLETED if not errors else TaskStatus.FAILED,
            result={
                "items": results,
                "summary": {
                    "total": len(results),
                    "succeeded": len(results) - len(errors),
                    "deleted": sum(1 for r in results if r.get("action") == "deleted"),
                    "skipped": sum(1 for r in results if r.get("action") == "skipped"),
                    "failed": len(errors),
                    "bytes_freed": total_bytes_freed,
                    "pattern_used": pattern if pattern else None,
                    "pipeline_used": use_pipeline and len(targets) > 1,
                },
            },
            error="; ".join(e.get("error", "") for e in errors) if errors else None,
            execution_time_ms=execution_time,
            parallel_calls=len(results),
        )

    def validate_task(self, task: SubagentTask) -> bool:
        """Validate downsert task."""
        payload = task.payload
        if not isinstance(payload, dict):
            return False
        # Must have either targets list or pattern
        has_targets = "targets" in payload and isinstance(payload["targets"], list)
        has_pattern = "pattern" in payload and isinstance(payload["pattern"], str)
        return has_targets or has_pattern


# Convenience functions for direct usage
def create_redis_executors(
    config: RedisConfig | None = None,
    default_ttl: int | None = 3600,  # 1 hour default
) -> tuple[RedisUpsertExecutor, RedisDownsertExecutor]:
    """Create configured Redis executors."""
    return (
        RedisUpsertExecutor(config=config, default_ttl=default_ttl),
        RedisDownsertExecutor(config=config),
    )


__all__ = [
    "RedisConfig",
    "RedisClientPool",
    "RedisDataType",
    "RedisUpsertItem",
    "RedisUpsertExecutor",
    "RedisDownsertExecutor",
    "create_redis_executors",
]
