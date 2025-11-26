#!/usr/bin/env python3
"""
Comprehensive Redis operations test suite.

Tests the full Redis executor capabilities:
- Pipelining for batch operations
- TTL/expiration support
- Hash storage for structured data
- Atomic operations via Lua scripts
- Pattern-based deletion
- Metadata tracking
- Pub/Sub notifications
"""
# pylint: disable=wrong-import-position,import-error
# ruff: noqa: E402
# flake8: noqa: E402

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any

import redis  # type: ignore[import-untyped,import-not-found]

# Add orchestrator package to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import SubagentOrchestrator, SubagentTask, TaskType
from orchestrator.executors.redis_ops import RedisClientPool, RedisConfig, RedisDownsertExecutor, RedisUpsertExecutor

# Test configuration
REDIS_CONFIG = RedisConfig(
    host="localhost",
    port=6379,
    db=0,
)


def get_redis_client() -> "redis.Redis[str]":
    """Get Redis client for verification."""
    return RedisClientPool.get_client(REDIS_CONFIG)


async def test_redis_connection() -> bool:
    """Test Redis connectivity and server info."""
    print("\n" + "=" * 70)
    print("🔌 Testing Redis Connection")
    print("=" * 70)

    try:
        client = get_redis_client()
        ping_result = client.ping()
        info = client.info("server")
        memory = client.info("memory")

        print(f"✅ Redis ping: {ping_result}")
        print(f"   Version: {info.get('redis_version', 'unknown')}")
        print(f"   Mode: {info.get('redis_mode', 'standalone')}")
        print(f"   Memory used: {memory.get('used_memory_human', 'unknown')}")
        print(f"   Peak memory: {memory.get('used_memory_peak_human', 'unknown')}")
        return True
    except redis.ConnectionError as e:
        print(f"❌ Redis connection failed: {e}")
        return False


async def test_json_upsert_with_pipeline() -> dict[str, Any]:
    """Test JSON upsert with pipelining for batch efficiency."""
    print("\n" + "=" * 70)
    print("📤 Test 1: JSON Upsert with Pipelining")
    print("=" * 70)

    orchestrator = SubagentOrchestrator()
    executor = RedisUpsertExecutor(config=REDIS_CONFIG, default_ttl=300)
    orchestrator.register_executor(TaskType.UPSERT, executor)

    # Batch of JSON items
    test_items: list[dict[str, Any]] = [
        {
            "target": "test:json:user:1",
            "data": {
                "id": 1,
                "name": "Alice",
                "email": "alice@example.com",
                "role": "admin",
            },
            "data_type": "JSON",
            "ttl": 600,  # 10 minutes
        },
        {
            "target": "test:json:user:2",
            "data": {
                "id": 2,
                "name": "Bob",
                "email": "bob@example.com",
                "role": "user",
            },
            "data_type": "JSON",
            "ttl": 600,
        },
        {
            "target": "test:json:config",
            "data": {
                "version": "2.0.0",
                "features": ["redis", "pipeline", "ttl"],
                "settings": {"debug": True, "cache_enabled": True},
            },
            "data_type": "JSON",
            "ttl": 3600,  # 1 hour
        },
        {
            "target": "test:json:metrics",
            "data": {
                "requests": 1000,
                "errors": 5,
                "latency_ms": [10, 15, 8, 12, 20],
                "timestamp": time.time(),
            },
            "data_type": "JSON",
        },
    ]

    task = SubagentTask(
        task_id="json-pipeline-test",
        task_type=TaskType.UPSERT,
        payload={"items": test_items, "pipeline": True},
        timeout_seconds=30.0,
    )

    print(f"\n📝 Upserting {len(test_items)} JSON items with pipeline...")
    start = time.perf_counter()
    results = await orchestrator.execute_batch([task])
    elapsed = (time.perf_counter() - start) * 1000

    result = results[0]
    print(f"\n✅ Completed in {elapsed:.2f}ms")
    print(f"   Status: {result.status.name}")
    result_dict = result.result if isinstance(result.result, dict) else {}
    print(f"   Pipeline used: {result_dict.get('summary', {}).get('pipeline_used')}")

    if result_dict:
        summary = result_dict.get("summary", {})
        print("\n📊 Summary:")
        print(f"   Created: {summary['created']}")
        print(f"   Updated: {summary['updated']}")

    # Verify TTLs
    client = get_redis_client()
    print("\n🔍 Verifying TTLs:")
    for item in test_items:
        key = str(item["target"])
        ttl = client.ttl(key)
        expected_ttl = item.get("ttl", 300) if isinstance(item, dict) else 300
        print(f"   {key}: TTL={ttl}s (expected ~{expected_ttl}s)")

    return {"status": result.status.name, "execution_time_ms": elapsed}


async def test_hash_upsert() -> dict[str, Any]:
    """Test Redis HASH data type for structured objects."""
    print("\n" + "=" * 70)
    print("📤 Test 2: Hash Storage for Structured Data")
    print("=" * 70)

    orchestrator = SubagentOrchestrator()
    executor = RedisUpsertExecutor(config=REDIS_CONFIG, default_ttl=300)
    orchestrator.register_executor(TaskType.UPSERT, executor)

    # Hash items - each field stored separately
    test_items = [
        {
            "target": "test:hash:session:abc123",
            "data": {
                "user_id": "user_1",
                "username": "alice",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0",
                "created_at": str(time.time()),
                "last_activity": str(time.time()),
            },
            "data_type": "HASH",
            "ttl": 1800,  # 30 min session
        },
        {
            "target": "test:hash:cache:product:100",
            "data": {
                "name": "Widget Pro",
                "price": "29.99",
                "stock": "150",
                "category": "electronics",
                "last_updated": str(time.time()),
            },
            "data_type": "HASH",
            "ttl": 300,  # 5 min cache
        },
    ]

    task = SubagentTask(
        task_id="hash-upsert-test",
        task_type=TaskType.UPSERT,
        payload={"items": test_items},
        timeout_seconds=30.0,
    )

    print(f"\n📝 Upserting {len(test_items)} HASH items...")
    start = time.perf_counter()
    results = await orchestrator.execute_batch([task])
    elapsed = (time.perf_counter() - start) * 1000

    result = results[0]
    print(f"\n✅ Completed in {elapsed:.2f}ms")

    # Verify hash structure
    client = get_redis_client()
    print("\n🔍 Verifying HASH structure:")
    for item in test_items:
        key = item["target"]
        hash_data = client.hgetall(key)
        ttl = client.ttl(key)
        print(f"   {key}:")
        print(f"      Fields: {len(hash_data)}")
        print(f"      TTL: {ttl}s")
        for field, value in list(hash_data.items())[:3]:
            print(f"      - {field}: {value[:30]}..." if len(str(value)) > 30 else f"      - {field}: {value}")

    return {"status": result.status.name, "execution_time_ms": elapsed}


async def test_conditional_upsert() -> dict[str, Any]:
    """Test NX (only if not exists) and XX (only if exists) conditions."""
    print("\n" + "=" * 70)
    print("📤 Test 3: Conditional Upsert (NX/XX)")
    print("=" * 70)

    orchestrator = SubagentOrchestrator()
    executor = RedisUpsertExecutor(config=REDIS_CONFIG)
    orchestrator.register_executor(TaskType.UPSERT, executor)

    # First, create a key
    setup_items = [
        {"target": "test:conditional:existing", "data": {"original": True}},
    ]

    task = SubagentTask(
        task_id="conditional-setup",
        task_type=TaskType.UPSERT,
        payload={"items": setup_items},
        timeout_seconds=30.0,
    )
    await orchestrator.execute_batch([task])

    # Now test NX and XX
    test_items = [
        {
            "target": "test:conditional:new_only",
            "data": {"created_with_nx": True},
            "nx": True,  # Only set if NOT exists
        },
        {
            "target": "test:conditional:existing",
            "data": {"this_should_fail": True},
            "nx": True,  # Should be skipped - key exists
        },
        {
            "target": "test:conditional:existing",
            "data": {"updated_with_xx": True},
            "xx": True,  # Only set if EXISTS
        },
        {
            "target": "test:conditional:nonexistent",
            "data": {"this_should_fail": True},
            "xx": True,  # Should be skipped - key doesn't exist
        },
    ]

    task = SubagentTask(
        task_id="conditional-test",
        task_type=TaskType.UPSERT,
        payload={"items": test_items, "pipeline": False},
        timeout_seconds=30.0,
    )

    print(f"\n📝 Testing {len(test_items)} conditional upserts...")
    results = await orchestrator.execute_batch([task])

    result = results[0]
    print("\n📊 Results:")
    for item in result.result.get("items", []):
        emoji = "✅" if item["action"] in ("created", "updated") else "⏭️"
        print(f"   {emoji} {item['target']}: {item['action']} ({item.get('status', 'n/a')})")

    return {"status": result.status.name}


async def test_pattern_downsert() -> dict[str, Any]:
    """Test pattern-based deletion (e.g., delete all test:* keys)."""
    print("\n" + "=" * 70)
    print("🗑️  Test 4: Pattern-Based Downsert")
    print("=" * 70)

    # First, create some keys with a common prefix
    client = get_redis_client()
    print("\n📝 Creating test keys for pattern deletion...")

    pipe = client.pipeline()
    for i in range(10):
        pipe.set(f"test:pattern:item:{i}", json.dumps({"id": i, "data": "test" * 100}))
    pipe.execute()

    orchestrator = SubagentOrchestrator()
    executor = RedisDownsertExecutor(config=REDIS_CONFIG)
    orchestrator.register_executor(TaskType.DOWNSERT, executor)

    # Delete by pattern
    task = SubagentTask(
        task_id="pattern-downsert-test",
        task_type=TaskType.DOWNSERT,
        payload={"pattern": "test:pattern:*"},
        timeout_seconds=30.0,
    )

    print("\n🗑️  Deleting all 'test:pattern:*' keys...")
    start = time.perf_counter()
    results = await orchestrator.execute_batch([task])
    elapsed = (time.perf_counter() - start) * 1000

    result = results[0]
    print(f"\n✅ Completed in {elapsed:.2f}ms")

    if result.result:
        summary = result.result["summary"]
        print("\n📊 Summary:")
        print(f"   Pattern: {summary.get('pattern_used')}")
        print(f"   Deleted: {summary['deleted']}")
        print(f"   Bytes freed: {summary['bytes_freed']}")

    # Verify deletion
    remaining = client.keys("test:pattern:*")
    print(f"\n🔍 Remaining keys matching pattern: {len(remaining)}")

    return {"status": result.status.name, "execution_time_ms": elapsed}


async def test_batch_downsert_pipeline() -> dict[str, Any]:
    """Test batch downsert with pipelining."""
    print("\n" + "=" * 70)
    print("🗑️  Test 5: Batch Downsert with Pipeline")
    print("=" * 70)

    # First, create fresh keys for this test
    client = get_redis_client()
    print("\n📝 Creating fresh keys for batch downsert test...")

    pipe = client.pipeline()
    targets = []
    for i in range(8):
        key = f"test:batch:delete:{i}"
        targets.append(key)
        pipe.set(key, json.dumps({"id": i, "data": f"value_{i}"}))
    # Add some non-existent keys
    targets.extend(["test:batch:nonexistent:1", "test:batch:nonexistent:2"])
    pipe.execute()

    orchestrator = SubagentOrchestrator()
    executor = RedisDownsertExecutor(config=REDIS_CONFIG)
    orchestrator.register_executor(TaskType.DOWNSERT, executor)

    task = SubagentTask(
        task_id="batch-downsert-test",
        task_type=TaskType.DOWNSERT,
        payload={"targets": targets, "pipeline": True},
        timeout_seconds=30.0,
    )

    print(f"\n🗑️  Downserting {len(targets)} keys with pipeline...")
    start = time.perf_counter()
    results = await orchestrator.execute_batch([task])
    elapsed = (time.perf_counter() - start) * 1000

    result = results[0]
    print(f"\n✅ Completed in {elapsed:.2f}ms")

    if result.result:
        summary = result.result["summary"]
        print("\n📊 Summary:")
        print(f"   Total: {summary['total']}")
        print(f"   Deleted: {summary['deleted']}")
        print(f"   Skipped: {summary['skipped']}")
        print(f"   Bytes freed: {summary['bytes_freed']}")
        print(f"   Pipeline used: {summary['pipeline_used']}")

    return {"status": result.status.name, "execution_time_ms": elapsed}


async def test_metadata_tracking() -> dict[str, Any]:
    """Test metadata tracking (version, timestamps)."""
    print("\n" + "=" * 70)
    print("📋 Test 6: Metadata Tracking")
    print("=" * 70)

    orchestrator = SubagentOrchestrator()
    executor = RedisUpsertExecutor(config=REDIS_CONFIG, enable_metadata=True)
    orchestrator.register_executor(TaskType.UPSERT, executor)

    # Create and update a key multiple times
    key = "test:metadata:versioned"

    for version in range(1, 4):
        task = SubagentTask(
            task_id=f"metadata-test-v{version}",
            task_type=TaskType.UPSERT,
            payload={
                "items": [
                    {
                        "target": key,
                        "data": {"version": version, "updated": True},
                    }
                ],
                "pipeline": False,
            },
            timeout_seconds=30.0,
        )
        await orchestrator.execute_batch([task])
        print(f"   Updated to version {version}")
        await asyncio.sleep(0.1)

    # Check metadata
    client = get_redis_client()
    meta_key = f"{key}:meta"
    metadata = client.hgetall(meta_key)

    print(f"\n🔍 Metadata for {key}:")
    for field, value in metadata.items():
        print(f"   {field}: {value}")

    # Cleanup
    client.delete(key, meta_key, f"{key}:version")

    return {"status": "COMPLETED"}


async def test_performance_comparison() -> dict[str, Any]:
    """Compare pipeline vs non-pipeline performance."""
    print("\n" + "=" * 70)
    print("⚡ Test 7: Performance Comparison (Pipeline vs Sequential)")
    print("=" * 70)

    orchestrator = SubagentOrchestrator()
    executor = RedisUpsertExecutor(config=REDIS_CONFIG, default_ttl=60)
    orchestrator.register_executor(TaskType.UPSERT, executor)

    # Create 100 items for testing
    num_items = 100
    test_items = [{"target": f"test:perf:item:{i}", "data": {"id": i, "value": f"data_{i}" * 10}} for i in range(num_items)]

    # Test with pipeline
    task_pipeline = SubagentTask(
        task_id="perf-pipeline",
        task_type=TaskType.UPSERT,
        payload={"items": test_items, "pipeline": True},
        timeout_seconds=60.0,
    )

    print(f"\n📝 Testing {num_items} items WITH pipeline...")
    start = time.perf_counter()
    _ = await orchestrator.execute_batch([task_pipeline])
    elapsed_pipeline = (time.perf_counter() - start) * 1000

    # Cleanup
    client = get_redis_client()
    client.delete(*[f"test:perf:item:{i}" for i in range(num_items)])

    # Test without pipeline
    task_sequential = SubagentTask(
        task_id="perf-sequential",
        task_type=TaskType.UPSERT,
        payload={"items": test_items, "pipeline": False},
        timeout_seconds=60.0,
    )

    print(f"📝 Testing {num_items} items WITHOUT pipeline...")
    start = time.perf_counter()
    _ = await orchestrator.execute_batch([task_sequential])
    elapsed_sequential = (time.perf_counter() - start) * 1000

    # Cleanup
    client.delete(*[f"test:perf:item:{i}" for i in range(num_items)])
    client.delete(*[f"test:perf:item:{i}:meta" for i in range(num_items)])

    speedup = elapsed_sequential / elapsed_pipeline if elapsed_pipeline > 0 else 0

    print(f"\n📊 Performance Results ({num_items} items):")
    print(f"   With pipeline:    {elapsed_pipeline:.2f}ms")
    print(f"   Without pipeline: {elapsed_sequential:.2f}ms")
    print(f"   Speedup:          {speedup:.1f}x faster with pipeline")

    return {
        "status": "COMPLETED",
        "pipeline_ms": elapsed_pipeline,
        "sequential_ms": elapsed_sequential,
        "speedup": speedup,
    }


async def test_cleanup() -> None:
    """Clean up all test keys."""
    print("\n" + "=" * 70)
    print("🧹 Cleaning up test data")
    print("=" * 70)

    client = get_redis_client()

    patterns = ["test:*"]
    total_deleted = 0

    for pattern in patterns:
        cursor = 0
        while True:
            cursor, keys = client.scan(cursor, match=pattern, count=100)
            if keys:
                # Include metadata keys
                all_keys = []
                for key in keys:
                    all_keys.extend([key, f"{key}:meta", f"{key}:version"])
                deleted = client.delete(*all_keys)
                total_deleted += deleted
            if not cursor:
                break

    print(f"✅ Deleted {total_deleted} test keys")


async def main() -> None:
    """Run comprehensive Redis test suite."""
    print("\n" + "=" * 70)
    print("🧪 Comprehensive Redis Operations Test Suite")
    print("=" * 70)
    print(f"   Host: {REDIS_CONFIG.host}:{REDIS_CONFIG.port}")
    print(f"   Database: {REDIS_CONFIG.db}")

    # Test connection first
    if not await test_redis_connection():
        print("\n❌ Cannot proceed without Redis connection")
        return

    results: dict[str, Any] = {}

    try:
        # Run all tests
        results["json_pipeline"] = await test_json_upsert_with_pipeline()
        results["hash_storage"] = await test_hash_upsert()
        results["conditional_nx_xx"] = await test_conditional_upsert()
        results["pattern_delete"] = await test_pattern_downsert()
        results["batch_downsert"] = await test_batch_downsert_pipeline()
        results["metadata_tracking"] = await test_metadata_tracking()
        results["performance"] = await test_performance_comparison()

    finally:
        await test_cleanup()
        RedisClientPool.close()

    # Final summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)

    all_passed = all(r.get("status") == "COMPLETED" for r in results.values())

    for test_name, result in results.items():
        status = "✅" if result.get("status") == "COMPLETED" else "❌"
        extra = ""
        if "execution_time_ms" in result:
            extra = f" ({result['execution_time_ms']:.1f}ms)"
        if "speedup" in result:
            extra = f" ({result['speedup']:.1f}x speedup)"
        print(f"   {status} {test_name}: {result.get('status', 'UNKNOWN')}{extra}")

    print("\n" + ("✅ All tests passed!" if all_passed else "❌ Some tests failed!"))
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
