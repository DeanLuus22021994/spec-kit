"""Redis-based embedding cache implementation."""

from __future__ import annotations

import hashlib
import importlib
import json
import logging
import time
import zlib
from typing import Any

from .config import CacheStrategy, EmbeddingCacheConfig
from .metrics import CacheMetrics

logger = logging.getLogger(__name__)

# Dynamic import to avoid static analysis errors if package is missing
redis: Any
try:
    redis = importlib.import_module("redis")
except ImportError:
    redis = None


class EmbeddingCache:
    """Redis-based cache for embeddings with compression and metrics."""

    _instance: EmbeddingCache | None = None
    _client: Any = None
    _initialized: bool = False

    def __new__(cls, config: EmbeddingCacheConfig | None = None) -> EmbeddingCache:
        """Singleton pattern for cache instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: EmbeddingCacheConfig | None = None) -> None:
        """Initialize embedding cache."""
        if getattr(self, "_initialized", False):
            return

        self.config = config or EmbeddingCacheConfig.from_env()
        self.metrics = CacheMetrics()
        self._latencies: list[float] = []
        self._connect()
        self._initialized = True

    def _connect(self) -> None:
        """Establish Redis connection."""
        if redis is None:
            logger.warning("Redis package not installed. Cache disabled.")
            self._client = None
            return

        try:
            pool = redis.ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                decode_responses=False,
                socket_timeout=5.0,
                max_connections=20,
            )
            self._client = redis.Redis(connection_pool=pool)
            if self._client is not None:
                self._client.ping()
            logger.info(
                "Embedding cache connected to Redis at %s:%d (db=%d)",
                self.config.host,
                self.config.port,
                self.config.db,
            )
        except redis.ConnectionError as e:
            logger.error("Failed to connect to Redis: %s", e)
            self._client = None

    @property
    def client(self) -> Any:
        """Get Redis client with auto-reconnect."""
        if self._client is None:
            self._connect()
        if self._client is None:
            raise RuntimeError("Redis connection unavailable")
        return self._client

    def _make_key(self, text: str, model: str) -> str:
        """Generate cache key from text and model."""
        content = f"{model}:{text}"
        hash_digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
        return f"{self.config.key_prefix}:{model}:{hash_digest}"

    def _compress(self, data: bytes) -> tuple[bytes, bool]:
        """Compress data if beneficial."""
        if not self.config.enable_compression:
            return data, False
        if len(data) < self.config.compression_threshold:
            return data, False

        compressed = zlib.compress(data, level=6)
        if len(compressed) < len(data) * 0.9:
            return compressed, True
        return data, False

    def _decompress(self, data: bytes, is_compressed: bool) -> bytes:
        """Decompress data if needed."""
        if is_compressed:
            return zlib.decompress(data)
        return data

    def _serialize_embedding(
        self, embedding: list[float], metadata: dict[str, Any] | None = None
    ) -> bytes:
        """Serialize embedding with optional metadata."""
        payload = {
            "v": embedding,
            "d": len(embedding),
            "t": time.time(),
        }
        if metadata:
            payload["m"] = metadata
        return json.dumps(payload).encode("utf-8")

    def _deserialize_embedding(self, data: bytes) -> tuple[list[float], dict[str, Any]]:
        """Deserialize embedding and metadata."""
        payload = json.loads(data.decode("utf-8"))
        metadata = {
            "dimensions": payload.get("d", len(payload["v"])),
            "cached_at": payload.get("t", 0),
            "extra": payload.get("m", {}),
        }
        return payload["v"], metadata

    def _track_latency(self, latency_ms: float) -> None:
        """Track operation latency for metrics."""
        self._latencies.append(latency_ms)
        if len(self._latencies) > 1000:
            self._latencies = self._latencies[-500:]
        self.metrics.avg_latency_ms = sum(self._latencies) / len(self._latencies)

    def get(
        self,
        text: str,
        model: str = "text-embedding-3-small",
    ) -> list[float] | None:
        """Get embedding from cache."""
        if redis is None:
            return None

        start = time.perf_counter()
        key = self._make_key(text, model)

        try:
            pipe = self.client.pipeline()
            pipe.get(key)
            pipe.get(f"{key}:z")
            results = pipe.execute()

            data = results[0]
            is_compressed = results[1] == b"1"

            if data is None:
                self.metrics.misses += 1
                return None

            decompressed = self._decompress(data, is_compressed)
            embedding, _ = self._deserialize_embedding(decompressed)

            self.metrics.hits += 1
            self._track_latency((time.perf_counter() - start) * 1000)

            if self.config.strategy in (CacheStrategy.LRU, CacheStrategy.HYBRID):
                self.client.touch(key)

            return embedding

        except (redis.RedisError, json.JSONDecodeError, zlib.error) as e:
            logger.warning("Cache get failed for key %s: %s", key, e)
            self.metrics.misses += 1
            return None

    def set(
        self,
        text: str,
        embedding: list[float],
        model: str = "text-embedding-3-small",
        ttl: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Cache an embedding."""
        if redis is None:
            return False

        start = time.perf_counter()
        key = self._make_key(text, model)
        effective_ttl = ttl if ttl is not None else self.config.default_ttl

        try:
            serialized = self._serialize_embedding(embedding, metadata)
            original_size = len(serialized)
            compressed, is_compressed = self._compress(serialized)
            final_size = len(compressed)

            pipe = self.client.pipeline()
            pipe.setex(key, effective_ttl, compressed)
            pipe.setex(f"{key}:z", effective_ttl, b"1" if is_compressed else b"0")
            pipe.execute()

            self.metrics.sets += 1
            if is_compressed:
                self.metrics.bytes_saved += original_size - final_size
                self.metrics.compression_ratio = original_size / final_size

            self._track_latency((time.perf_counter() - start) * 1000)
            return True

        except redis.RedisError as e:
            logger.error("Cache set failed for key %s: %s", key, e)
            return False

    def get_many(
        self,
        texts: list[str],
        model: str = "text-embedding-3-small",
    ) -> dict[str, list[float] | None]:
        """Get multiple embeddings from cache."""
        if not texts or redis is None:
            return {}

        start = time.perf_counter()
        keys = [self._make_key(text, model) for text in texts]
        results: dict[str, list[float] | None] = {}

        try:
            pipe = self.client.pipeline()
            for key in keys:
                pipe.get(key)
                pipe.get(f"{key}:z")
            responses = pipe.execute()

            for i, text in enumerate(texts):
                data = responses[i * 2]
                is_compressed = responses[i * 2 + 1] == b"1"

                if data is None:
                    results[text] = None
                    self.metrics.misses += 1
                else:
                    try:
                        decompressed = self._decompress(data, is_compressed)
                        embedding, _ = self._deserialize_embedding(decompressed)
                        results[text] = embedding
                        self.metrics.hits += 1
                    except (json.JSONDecodeError, zlib.error):
                        results[text] = None
                        self.metrics.misses += 1

            self._track_latency((time.perf_counter() - start) * 1000)
            return results

        except redis.RedisError as e:
            logger.error("Batch cache get failed: %s", e)
            return {text: None for text in texts}

    def set_many(
        self,
        items: list[tuple[str, list[float]]],
        model: str = "text-embedding-3-small",
        ttl: int | None = None,
    ) -> int:
        """Cache multiple embeddings."""
        if not items or redis is None:
            return 0

        start = time.perf_counter()
        effective_ttl = ttl if ttl is not None else self.config.default_ttl
        success_count = 0

        try:
            pipe = self.client.pipeline()

            for text, embedding in items:
                key = self._make_key(text, model)
                serialized = self._serialize_embedding(embedding)
                compressed, is_compressed = self._compress(serialized)

                pipe.setex(key, effective_ttl, compressed)
                pipe.setex(f"{key}:z", effective_ttl, b"1" if is_compressed else b"0")

            results = pipe.execute()
            success_count = sum(1 for r in results[::2] if r)
            self.metrics.sets += success_count

            self._track_latency((time.perf_counter() - start) * 1000)
            return success_count

        except redis.RedisError as e:
            logger.error("Batch cache set failed: %s", e)
            return 0

    def delete(self, text: str, model: str = "text-embedding-3-small") -> bool:
        """Delete a cached embedding."""
        if redis is None:
            return False
        key = self._make_key(text, model)
        try:
            deleted = self.client.delete(key, f"{key}:z")
            if deleted > 0:
                self.metrics.deletes += 1
            return bool(deleted > 0)
        except redis.RedisError as e:
            logger.error("Cache delete failed: %s", e)
            return False

    def clear(self, model: str | None = None) -> int:
        """Clear cached embeddings."""
        if redis is None:
            return 0
        pattern = (
            f"{self.config.key_prefix}:{model}:*"
            if model
            else f"{self.config.key_prefix}:*"
        )
        total_deleted = 0

        try:
            cursor = 0
            while True:
                cursor, keys = self.client.scan(cursor, match=pattern, count=100)
                if keys:
                    all_keys = []
                    for key in keys:
                        all_keys.append(key)
                        if not key.endswith(b":z"):
                            all_keys.append(key + b":z")
                    deleted = self.client.delete(*all_keys)
                    total_deleted += deleted
                if not cursor:
                    break

            self.metrics.deletes += total_deleted
            return total_deleted

        except redis.RedisError as e:
            logger.error("Cache clear failed: %s", e)
            return 0

    def exists(self, text: str, model: str = "text-embedding-3-small") -> bool:
        """Check if embedding is cached."""
        if redis is None:
            return False
        key = self._make_key(text, model)
        try:
            return bool(self.client.exists(key))
        except redis.RedisError:
            return False

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        if redis is None:
            return {"error": "Redis not available", "metrics": self.metrics.to_dict()}

        try:
            info = self.client.info("memory")
            db_info = self.client.info("keyspace").get(f"db{self.config.db}", {})

            return {
                "metrics": self.metrics.to_dict(),
                "redis": {
                    "memory_used": info.get("used_memory_human", "unknown"),
                    "peak_memory": info.get("used_memory_peak_human", "unknown"),
                    "keys": db_info.get("keys", 0) if isinstance(db_info, dict) else 0,
                },
                "config": {
                    "key_prefix": self.config.key_prefix,
                    "default_ttl": self.config.default_ttl,
                    "compression_enabled": self.config.enable_compression,
                },
            }
        except redis.RedisError as e:
            return {"error": str(e), "metrics": self.metrics.to_dict()}

    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self.metrics = CacheMetrics()
        self._latencies.clear()

    def health_check(self) -> dict[str, Any]:
        """Check cache health."""
        if redis is None:
            return {
                "status": "disabled",
                "error": "Redis package not installed",
                "connected": False,
            }

        try:
            start = time.perf_counter()
            self.client.ping()
            latency = (time.perf_counter() - start) * 1000

            return {
                "status": "healthy",
                "latency_ms": f"{latency:.2f}",
                "hit_rate": f"{self.metrics.hit_rate:.2%}",
                "connected": True,
            }
        except redis.RedisError as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connected": False,
            }

    def close(self) -> None:
        """Close the cache connection."""
        if self._client:
            self._client.close()
            self._client = None
            EmbeddingCache._instance = None
            logger.info("Embedding cache connection closed")


def get_embedding_cache(config: EmbeddingCacheConfig | None = None) -> EmbeddingCache:
    """Get the embedding cache singleton."""
    return EmbeddingCache(config)
