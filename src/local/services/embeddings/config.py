"""Configuration for embedding cache."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum, auto


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
    def from_env(cls) -> EmbeddingCacheConfig:
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
