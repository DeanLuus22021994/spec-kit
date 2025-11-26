#!/usr/bin/env python3
"""Test the embedding cache functionality."""

from __future__ import annotations

import time

from services.embeddings.cache import EmbeddingCache
from services.embeddings.config import EmbeddingCacheConfig


def run_basic_set_get(cache: EmbeddingCache) -> str:
    test_text = "Hello, this is a test embedding"
    test_embedding = [0.1 * i for i in range(1536)]
    start = time.perf_counter()
    success = cache.set(test_text, test_embedding, model="text-embedding-3-small")
    set_time = (time.perf_counter() - start) * 1000
    print(f"   Set: {'✅' if success else '❌'} ({set_time:.2f}ms)")
    start = time.perf_counter()
    retrieved = cache.get(test_text, model="text-embedding-3-small")
    get_time = (time.perf_counter() - start) * 1000
    print(f"   Get: {'✅' if retrieved else '❌'} ({get_time:.2f}ms)")
    if retrieved:
        match = retrieved == test_embedding
        print(f"   Match: {'✅' if match else '❌'} (dim={len(retrieved)})")
    return test_text


def run_hit_miss(cache: EmbeddingCache, test_text: str) -> None:
    cache.reset_metrics()
    _ = cache.get("nonexistent text")
    _ = cache.get(test_text)
    _ = cache.get(test_text)
    stats = cache.get_stats()
    print(f"   Hits: {stats['metrics']['hits']}")
    print(f"   Misses: {stats['metrics']['misses']}")
    print(f"   Hit Rate: {stats['metrics']['hit_rate']}")


def run_batch_ops(cache: EmbeddingCache) -> None:
    batch_items = [
        (f"batch text {i}", [0.01 * j for j in range(1536)]) for i in range(10)
    ]
    start = time.perf_counter()
    count = cache.set_many(batch_items)
    batch_set_time = (time.perf_counter() - start) * 1000
    print(f"   Set 10 items: {count}/10 ({batch_set_time:.2f}ms)")
    texts = [item[0] for item in batch_items]
    start = time.perf_counter()
    results = cache.get_many(texts)
    batch_get_time = (time.perf_counter() - start) * 1000
    hits = sum(1 for v in results.values() if v is not None)
    print(f"   Get 10 items: {hits}/10 ({batch_get_time:.2f}ms)")


def run_compression(cache: EmbeddingCache) -> None:
    large_text = "Large embedding test " * 100
    large_embedding = [0.001 * i for i in range(3072)]
    cache.set(large_text, large_embedding, model="text-embedding-3-large")
    stats = cache.get_stats()
    print(f"   Bytes saved: {stats['metrics']['bytes_saved']}")
    print(f"   Compression ratio: {stats['metrics']['compression_ratio']}")


def run_delete_clear(cache: EmbeddingCache, test_text: str) -> None:
    deleted = cache.delete(test_text)
    print(f"   Delete single: {'✅' if deleted else '❌'}")
    exists = cache.exists(test_text)
    print(
        f"   Exists after delete: {'❌ (expected)' if not exists else '⚠️ Still exists'}"
    )
    cleared = cache.clear(model="text-embedding-3-small")
    print(f"   Cleared {cleared} keys for text-embedding-3-small")
    cleared = cache.clear()
    print(f"   Cleared {cleared} remaining test keys")


def test_embedding_cache() -> None:
    """Test embedding cache operations."""
    print("\n" + "=" * 70)
    print("🧪 Embedding Cache Test Suite")
    print("=" * 70)

    # Configure for test
    config = EmbeddingCacheConfig(
        host="localhost",
        port=6379,
        db=2,  # Use test DB
        key_prefix="test:emb",
        default_ttl=60,  # 1 minute for tests
        enable_compression=True,
    )

    cache = EmbeddingCache(config)

    # Health check
    print("\n📍 Health Check")
    health = cache.health_check()
    print(f"   Status: {health['status']}")
    if health["status"] != "healthy":
        print(f"   ❌ Cache unhealthy: {health.get('error', 'unknown')}")
        return

    # Test 1: Basic set/get
    print("\n📤 Test 1: Basic Set/Get")
    test_text = "Hello, this is a test embedding"
    test_embedding = [0.1 * i for i in range(1536)]  # 1536-dim vector

    start = time.perf_counter()
    success = cache.set(test_text, test_embedding, model="text-embedding-3-small")
    set_time = (time.perf_counter() - start) * 1000
    print(f"   Set: {'✅' if success else '❌'} ({set_time:.2f}ms)")

    start = time.perf_counter()
    retrieved = cache.get(test_text, model="text-embedding-3-small")
    get_time = (time.perf_counter() - start) * 1000
    print(f"   Get: {'✅' if retrieved else '❌'} ({get_time:.2f}ms)")

    if retrieved:
        match = retrieved == test_embedding
        print(f"   Match: {'✅' if match else '❌'} (dim={len(retrieved)})")

    # Test 2: Cache hit/miss
    print("\n📊 Test 2: Cache Hit/Miss")
    cache.reset_metrics()

    # Miss
    _ = cache.get("nonexistent text")
    # Hit
    _ = cache.get(test_text)
    _ = cache.get(test_text)

    stats = cache.get_stats()
    print(f"   Hits: {stats['metrics']['hits']}")
    print(f"   Misses: {stats['metrics']['misses']}")
    print(f"   Hit Rate: {stats['metrics']['hit_rate']}")

    # Test 3: Batch operations
    print("\n📦 Test 3: Batch Operations")
    run_batch_ops(cache)

    # Test 4: Compression
    print("\n🗜️  Test 4: Compression")
    run_compression(cache)

    # Test 5: Delete
    print("\n🗑️  Test 5: Delete")
    deleted = cache.delete(test_text)
    print(f"   Delete single: {'✅' if deleted else '❌'}")

    exists = cache.exists(test_text)
    print(
        f"   Exists after delete: {'❌ (expected)' if not exists else '⚠️ Still exists'}"
    )

    # Test 6: Clear by model
    run_delete_clear(cache, test_text)

    # Final stats
    print("\n📈 Final Statistics")
    final_stats = cache.get_stats()
    print(f"   Total hits: {final_stats['metrics']['hits']}")
    print(f"   Total misses: {final_stats['metrics']['misses']}")
    print(f"   Total sets: {final_stats['metrics']['sets']}")
    print(f"   Avg latency: {final_stats['metrics']['avg_latency_ms']}")
    print(f"   Redis memory: {final_stats['redis']['memory_used']}")

    # Cleanup
    cache.close()

    print("\n✅ All tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    test_embedding_cache()
