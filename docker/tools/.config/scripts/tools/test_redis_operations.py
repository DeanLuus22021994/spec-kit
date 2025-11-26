#!/usr/bin/env python3
"""
Test Redis-backed upsert and downsert operations.

This script tests the orchestrator's upsert/downsert executors
with Redis as the storage backend instead of file system.
"""
# pylint: disable=wrong-import-position,import-error
# ruff: noqa: E402

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

from orchestrator import SubagentOrchestrator, SubagentTask, TaskType  # noqa: E402
from orchestrator.executors.file_ops import DownsertExecutor, UpsertExecutor  # noqa: E402

# Redis connection configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# Create Redis client
redis_client: redis.Redis[str] = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,
)


def redis_upsert(key: str, data: Any) -> dict[str, Any]:
    """
    Upsert data to Redis (create or update).

    Args:
        key: Redis key to set
        data: Data to store (will be JSON serialized if dict)

    Returns:
        Result dict with action taken
    """
    existed = redis_client.exists(key) > 0

    if isinstance(data, dict):
        value = json.dumps(data)
    elif isinstance(data, str):
        value = data
    else:
        value = str(data)

    redis_client.set(key, value)

    return {
        "target": key,
        "action": "updated" if existed else "created",
        "size_bytes": len(value),
        "ttl": redis_client.ttl(key),
    }


def redis_downsert(key: str) -> dict[str, Any]:
    """
    Downsert (delete if exists) from Redis.

    Args:
        key: Redis key to delete

    Returns:
        Result dict with action taken
    """
    existed = redis_client.exists(key) > 0

    if existed:
        redis_client.delete(key)

    return {
        "target": key,
        "action": "deleted" if existed else "skipped",
        "existed": existed,
    }


async def test_redis_connection() -> bool:
    """Test Redis connectivity."""
    print("\n" + "=" * 60)
    print("🔌 Testing Redis Connection")
    print("=" * 60)

    try:
        ping_result = redis_client.ping()
        info = redis_client.info("server")
        print(f"✅ Redis ping: {ping_result}")
        print(f"   Version: {info.get('redis_version', 'unknown')}")
        print(f"   Mode: {info.get('redis_mode', 'unknown')}")
        return True
    except redis.ConnectionError as e:
        print(f"❌ Redis connection failed: {e}")
        return False


async def test_upsert_operations() -> dict[str, Any]:
    """Test Redis upsert operations."""
    print("\n" + "=" * 60)
    print("📤 Testing UPSERT Operations")
    print("=" * 60)

    # Create orchestrator with Redis upsert function
    orchestrator = SubagentOrchestrator()
    executor = UpsertExecutor(upsert_func=redis_upsert)
    orchestrator.register_executor(TaskType.UPSERT, executor)

    # Test data
    test_items = [
        {
            "target": "test:user:1",
            "data": {"id": 1, "name": "Alice", "email": "alice@example.com"},
        },
        {
            "target": "test:user:2",
            "data": {"id": 2, "name": "Bob", "email": "bob@example.com"},
        },
        {
            "target": "test:config:app",
            "data": {
                "version": "1.0.0",
                "debug": True,
                "features": ["upsert", "downsert"],
            },
        },
        {
            "target": "test:simple:string",
            "data": "Hello, Redis!",
        },
        {
            "target": "test:embedding:001",
            "data": {
                "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
                "metadata": {"source": "test"},
            },
        },
    ]

    # Create upsert task
    task = SubagentTask(
        task_id="redis-upsert-test-001",
        task_type=TaskType.UPSERT,
        payload={"items": test_items},
        timeout_seconds=30.0,
    )

    print(f"\n📝 Upserting {len(test_items)} items to Redis...")
    start = time.perf_counter()

    results = await orchestrator.execute_batch([task])

    elapsed = (time.perf_counter() - start) * 1000

    result = results[0]
    print(f"\n✅ Upsert completed in {elapsed:.2f}ms")
    print(f"   Status: {result.status.name}")
    print(f"   Parallel calls: {result.parallel_calls}")

    if result.result:
        summary = result.result.get("summary", {})
        print("\n📊 Summary:")
        print(f"   Total: {summary.get('total', 0)}")
        print(f"   Succeeded: {summary.get('succeeded', 0)}")
        print(f"   Created: {summary.get('created', 0)}")
        print(f"   Updated: {summary.get('updated', 0)}")

        print("\n📋 Items:")
        for item in result.result.get("items", []):
            print(f"   - {item['target']}: {item['action']} ({item['size_bytes']} bytes)")

    # Verify data in Redis
    print("\n🔍 Verifying data in Redis:")
    for item in test_items:
        key = item["target"]
        value = redis_client.get(key)
        print(f"   {key}: {value[:50]}..." if len(str(value)) > 50 else f"   {key}: {value}")

    return {
        "status": result.status.name,
        "execution_time_ms": elapsed,
        "items_processed": len(test_items),
    }


async def test_upsert_update() -> dict[str, Any]:
    """Test updating existing Redis keys."""
    print("\n" + "=" * 60)
    print("🔄 Testing UPSERT Update (existing keys)")
    print("=" * 60)

    orchestrator = SubagentOrchestrator()
    executor = UpsertExecutor(upsert_func=redis_upsert)
    orchestrator.register_executor(TaskType.UPSERT, executor)

    # Update existing items
    update_items = [
        {
            "target": "test:user:1",
            "data": {
                "id": 1,
                "name": "Alice Updated",
                "email": "alice.new@example.com",
                "updated": True,
            },
        },
        {
            "target": "test:config:app",
            "data": {
                "version": "2.0.0",
                "debug": False,
                "features": ["upsert", "downsert", "redis"],
            },
        },
    ]

    task = SubagentTask(
        task_id="redis-upsert-update-001",
        task_type=TaskType.UPSERT,
        payload={"items": update_items},
        timeout_seconds=30.0,
    )

    print(f"\n📝 Updating {len(update_items)} existing items...")
    results = await orchestrator.execute_batch([task])

    result = results[0]
    print("✅ Update completed")
    print(f"   Status: {result.status.name}")

    if result.result:
        summary = result.result.get("summary", {})
        print(f"   Created: {summary.get('created', 0)} (should be 0)")
        print(f"   Updated: {summary.get('updated', 0)} (should be 2)")

    # Verify updates
    print("\n🔍 Verifying updates:")
    for item in update_items:
        key = item["target"]
        value = redis_client.get(key)
        data = json.loads(value) if value else None
        if data:
            print(f"   {key}: {data}")

    return {"status": result.status.name}


async def test_downsert_operations() -> dict[str, Any]:
    """Test Redis downsert operations."""
    print("\n" + "=" * 60)
    print("📥 Testing DOWNSERT Operations")
    print("=" * 60)

    orchestrator = SubagentOrchestrator()
    executor = DownsertExecutor(downsert_func=redis_downsert)
    orchestrator.register_executor(TaskType.DOWNSERT, executor)

    # Keys to delete (some exist, some don't)
    targets = [
        "test:user:1",
        "test:user:2",
        "test:nonexistent:key",  # Should be skipped
    ]

    task = SubagentTask(
        task_id="redis-downsert-test-001",
        task_type=TaskType.DOWNSERT,
        payload={"targets": targets},
        timeout_seconds=30.0,
    )

    print(f"\n🗑️  Downserting {len(targets)} keys from Redis...")
    start = time.perf_counter()

    results = await orchestrator.execute_batch([task])

    elapsed = (time.perf_counter() - start) * 1000

    result = results[0]
    print(f"\n✅ Downsert completed in {elapsed:.2f}ms")
    print(f"   Status: {result.status.name}")

    if result.result:
        summary = result.result.get("summary", {})
        print("\n📊 Summary:")
        print(f"   Total: {summary.get('total', 0)}")
        print(f"   Succeeded: {summary.get('succeeded', 0)}")
        print(f"   Deleted: {summary.get('deleted', 0)}")
        print(f"   Skipped: {summary.get('skipped', 0)}")

        print("\n📋 Items:")
        for item in result.result.get("items", []):
            emoji = "🗑️ " if item["action"] == "deleted" else "⏭️ "
            print(f"   {emoji}{item['target']}: {item['action']}")

    # Verify deletion
    print("\n🔍 Verifying deletions:")
    for key in targets:
        exists = redis_client.exists(key)
        status = "❌ deleted" if not exists else "✅ still exists"
        print(f"   {key}: {status}")

    return {
        "status": result.status.name,
        "execution_time_ms": elapsed,
    }


async def test_cleanup() -> None:
    """Clean up all test keys."""
    print("\n" + "=" * 60)
    print("🧹 Cleaning up test data")
    print("=" * 60)

    # Find and delete all test keys
    pattern = "test:*"
    keys = redis_client.keys(pattern)

    if keys:
        deleted = redis_client.delete(*keys)
        print(f"✅ Deleted {deleted} test keys matching '{pattern}'")
    else:
        print(f"ℹ️  No keys found matching '{pattern}'")


async def main() -> None:
    """Run all Redis upsert/downsert tests."""
    print("\n" + "=" * 60)
    print("🧪 Redis Upsert/Downsert Test Suite")
    print("=" * 60)
    print(f"   Host: {REDIS_HOST}:{REDIS_PORT}")
    print(f"   Database: {REDIS_DB}")

    # Test Redis connection first
    if not await test_redis_connection():
        print("\n❌ Cannot proceed without Redis connection")
        return

    results = {}

    try:
        # Run tests
        results["upsert_create"] = await test_upsert_operations()
        results["upsert_update"] = await test_upsert_update()
        results["downsert"] = await test_downsert_operations()

    finally:
        # Always cleanup
        await test_cleanup()

    # Final summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    all_passed = all(r.get("status") == "COMPLETED" for r in results.values())

    for test_name, result in results.items():
        status = "✅" if result.get("status") == "COMPLETED" else "❌"
        print(f"   {status} {test_name}: {result.get('status', 'UNKNOWN')}")

    print("\n" + ("✅ All tests passed!" if all_passed else "❌ Some tests failed!"))
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
