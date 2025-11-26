"""Embeddings package for semantic-kernel-app.

This package provides embedding generation and management
functionality using OpenAI's text-embedding models.

Includes Redis-based caching for performance optimization.
"""

from .cache import EmbeddingCache, get_embedding_cache
from .config import CacheStrategy, EmbeddingCacheConfig
from .metrics import CacheMetrics

__all__ = [
    "EmbeddingCache",
    "EmbeddingCacheConfig",
    "CacheMetrics",
    "CacheStrategy",
    "get_embedding_cache",
]
