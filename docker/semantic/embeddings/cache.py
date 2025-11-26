"""Redis-based embedding cache for semantic operations.

This module provides caching for embeddings to:
- Reduce API costs (embeddings are expensive to generate)
- Improve latency (cache hits are ~100x faster)
- Enable offline operation (cached embeddings work without API)
- Track usage patterns and hit rates

Features:
- Content-based hashing for cache keys
- TTL-based expiration for freshness
- Batch operations with pipelining
- Compression for large embeddings
- Metrics and hit rate tracking
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import zlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any

import redis  # type: ignore[import-not-found]

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache eviction/storage strategy."""

    LRU = auto()  # Least Recently Used (default)
    LFU = auto()  # Least Frequently Used
    TTL = auto()  # Time-based expiration only
    HYBRID = auto()  # LRU + TTL


@dataclass
class EmbeddingCacheConfig:
    """Configuration for embedding cache."""

    host: str = "localhost"
    port: int = 6379
    db: int = 1  # Use separate DB for embeddings
    password: str | None = None
    key_prefix: str = "emb"
    default_ttl: int = 86400 * 7  # 7 days default
    max_memory_mb: int = 512
    enable_compression: bool = True
    compression_threshold: int = 1024  # Compress if > 1KB
    enable_metrics: bool = True
    strategy: CacheStrategy = CacheStrategy.HYBRID

    @classmethod
    def from_env(cls) -> "EmbeddingCacheConfig":
        """Load configuration from environment."""
        return cls(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_EMBEDDINGS_DB", "1")),
            password=os.getenv("REDIS_PASSWORD"),
            key_prefix=os.getenv("REDIS_EMBEDDING_PREFIX", "emb"),
            default_ttl=int(os.getenv("REDIS_EMBEDDING_TTL", "604800")),
            enable_compression=os.getenv("REDIS_EMBEDDING_COMPRESS", "true").lower()
            == "true",
        )


@dataclass
class CacheMetrics:
    """Cache performance metrics."""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    bytes_saved: int = 0
    compression_ratio: float = 1.0
    avg_latency_ms: float = 0.0
    last_reset: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "hit_rate": f"{self.hit_rate:.2%}",
            "bytes_saved": self.bytes_saved,
            "compression_ratio": f"{self.compression_ratio:.2f}",
            "avg_latency_ms": f"{self.avg_latency_ms:.2f}",
            "last_reset": self.last_reset,
        }


class EmbeddingCache:  # pylint: disable=too-many-instance-attributes
    """Redis-based cache for embeddings with compression and metrics.

    Example usage:
        cache = EmbeddingCache()

        # Cache an embedding
        cache.set("Hello world", [0.1, 0.2, ...], model="text-embedding-3-small")

        # Retrieve from cache
        embedding = cache.get("Hello world", model="text-embedding-3-small")

        # Batch operations
        results = cache.get_many(["text1", "text2", "text3"])
    """

    _instance: "EmbeddingCache | None" = None
    _client: "redis.Redis[bytes] | None" = None

    def __new__(cls, config: EmbeddingCacheConfig | None = None) -> "EmbeddingCache":
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
        try:
            pool = redis.ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                decode_responses=False,  # We handle bytes for compression
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
    def client(self) -> "redis.Redis[bytes]":
        """Get Redis client with auto-reconnect."""
        if self._client is None:
            self._connect()
        if self._client is None:
            raise RuntimeError("Redis connection unavailable")
        return self._client

    def _make_key(self, text: str, model: str) -> str:
        """Generate cache key from text and model.

        Uses SHA-256 hash of text + model for consistent keys.
        """
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
        if len(compressed) < len(data) * 0.9:  # At least 10% savings
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
            "v": embedding,  # vector
            "d": len(embedding),  # dimensions
            "t": time.time(),  # timestamp
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
        """Get embedding from cache.

        Args:
            text: The text that was embedded
            model: The embedding model used

        Returns:
            The cached embedding vector, or None if not found
        """
        start = time.perf_counter()
        key = self._make_key(text, model)

        try:
            # Get data and compression flag
            pipe = self.client.pipeline()
            pipe.get(key)
            pipe.get(f"{key}:z")  # Compression flag
            results = pipe.execute()

            data = results[0]
            is_compressed = results[1] == b"1"

            if data is None:
                self.metrics.misses += 1
                return None

            # Decompress and deserialize
            decompressed = self._decompress(data, is_compressed)
            embedding, _ = self._deserialize_embedding(decompressed)

            self.metrics.hits += 1
            self._track_latency((time.perf_counter() - start) * 1000)

            # Update access time for LRU
            if self.config.strategy in (CacheStrategy.LRU, CacheStrategy.HYBRID):
                self.client.touch(key)

            return embedding

        except (redis.RedisError, json.JSONDecodeError, zlib.error) as e:
            logger.warning("Cache get failed for key %s: %s", key, e)
            self.metrics.misses += 1
            return None

    def set(  # pylint: disable=too-many-locals
        self,
        text: str,
        embedding: list[float],
        model: str = "text-embedding-3-small",
        ttl: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Cache an embedding.

        Args:
            text: The original text
            embedding: The embedding vector
            model: The model used
            ttl: Time-to-live in seconds (None uses default)
            metadata: Additional metadata to store

        Returns:
            True if cached successfully
        """
        start = time.perf_counter()
        key = self._make_key(text, model)
        effective_ttl = ttl if ttl is not None else self.config.default_ttl

        try:
            # Serialize and optionally compress
            serialized = self._serialize_embedding(embedding, metadata)
            original_size = len(serialized)
            compressed, is_compressed = self._compress(serialized)
            final_size = len(compressed)

            # Store with pipeline
            pipe = self.client.pipeline()
            pipe.setex(key, effective_ttl, compressed)
            pipe.setex(f"{key}:z", effective_ttl, b"1" if is_compressed else b"0")
            pipe.execute()

            # Track metrics
            self.metrics.sets += 1
            if is_compressed:
                self.metrics.bytes_saved += original_size - final_size
                self.metrics.compression_ratio = original_size / final_size

            self._track_latency((time.perf_counter() - start) * 1000)
            return True

        except redis.RedisError as e:
            logger.error("Cache set failed for key %s: %s", key, e)
            return False

    def get_many(  # pylint: disable=too-many-locals
        self,
        texts: list[str],
        model: str = "text-embedding-3-small",
    ) -> dict[str, list[float] | None]:
        """Get multiple embeddings from cache.

        Args:
            texts: List of texts to look up
            model: The embedding model

        Returns:
            Dict mapping text to embedding (None if not cached)
        """
        if not texts:
            return {}

        start = time.perf_counter()
        keys = [self._make_key(text, model) for text in texts]
        results: dict[str, list[float] | None] = {}

        try:
            # Batch get with pipeline
            pipe = self.client.pipeline()
            for key in keys:
                pipe.get(key)
                pipe.get(f"{key}:z")
            responses = pipe.execute()

            # Process results
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

    def set_many(  # pylint: disable=too-many-locals
        self,
        items: list[tuple[str, list[float]]],
        model: str = "text-embedding-3-small",
        ttl: int | None = None,
    ) -> int:
        """Cache multiple embeddings.

        Args:
            items: List of (text, embedding) tuples
            model: The embedding model
            ttl: Time-to-live in seconds

        Returns:
            Number of items successfully cached
        """
        if not items:
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
        """Delete a cached embedding.

        Args:
            text: The original text
            model: The embedding model

        Returns:
            True if deleted
        """
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
        """Clear cached embeddings.

        Args:
            model: If specified, only clear for this model

        Returns:
            Number of keys deleted
        """
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
                    # Include compression flag keys
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
        """Check if embedding is cached.

        Args:
            text: The original text
            model: The embedding model

        Returns:
            True if cached
        """
        key = self._make_key(text, model)
        try:
            return bool(self.client.exists(key))
        except redis.RedisError:
            return False

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats and metrics
        """
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
        """Check cache health.

        Returns:
            Health status dictionary
        """
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


# Convenience function for getting cache instance
def get_embedding_cache(config: EmbeddingCacheConfig | None = None) -> EmbeddingCache:
    """Get the embedding cache singleton.

    Args:
        config: Optional configuration (only used on first call)

    Returns:
        The embedding cache instance
    """
    return EmbeddingCache(config)


__all__ = [
    "EmbeddingCache",
    "EmbeddingCacheConfig",
    "CacheMetrics",
    "CacheStrategy",
    "get_embedding_cache",
]
