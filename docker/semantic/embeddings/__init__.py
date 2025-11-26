"""Embeddings package for semantic-kernel-app.

This package provides embedding generation and management
functionality using OpenAI's text-embedding models.

Includes Redis-based caching for performance optimization.
"""

from semantic.embeddings.cache import CacheMetrics, CacheStrategy, EmbeddingCache, EmbeddingCacheConfig, get_embedding_cache

__all__ = [
    "EmbeddingCache",
    "EmbeddingCacheConfig",
    "CacheMetrics",
    "CacheStrategy",
    "get_embedding_cache",
]
