#!/usr/bin/env python3
"""CLI entry point for the subagent orchestrator."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from .api import (
    batch_downsert,
    batch_upsert,
    create_full_orchestrator,
    run_gpu_inference,
    sync_registry,
)
from .config import GPU_CONFIG, PRECOMPILED_IMAGES, SubagentConfig, SubagentTask
from .orchestrator import XMLTemplateRenderer


def main() -> None:
    """CLI entry point for testing."""
    parser = argparse.ArgumentParser(
        description="Subagent Orchestrator CLI - RTX Compute & Registry Integration"
    )
    parser.add_argument("--profile", default="development", help="Execution profile")
    parser.add_argument("--config", type=Path, help="Config file path")
    parser.add_argument(
        "--task-config",
        help="JSON string containing task configuration for generic execution",
    )
    parser.add_argument("--list-templates", action="store_true", help="List templates")
    parser.add_argument(
        "--list-images", action="store_true", help="List precompiled images"
    )
    parser.add_argument(
        "--gpu-check", action="store_true", help="Check GPU availability"
    )
    parser.add_argument(
        "--registry-list", action="store_true", help="List registry images"
    )
    parser.add_argument(
        "--run-gpu-inference",
        metavar="MODEL",
        help="Run GPU inference (arcface|embeddings|vector)",
    )
    parser.add_argument(
        "--upsert",
        nargs=2,
        metavar=("TARGET", "DATA"),
        help="Upsert a single file",
    )
    parser.add_argument(
        "--downsert",
        metavar="TARGET",
        help="Downsert (delete if exists) a single target",
    )
    args = parser.parse_args()

    if args.config:
        SubagentConfig.load(args.config)

    if args.task_config:
        try:
            task_data = json.loads(args.task_config)
            task = SubagentTask(**task_data)
            orchestrator = create_full_orchestrator()
            print(f"Executing task: {task.task_type}")
            results = asyncio.run(orchestrator.execute_batch([task]))
            print(json.dumps(results[0], default=lambda o: o.__dict__, indent=2))
        except json.JSONDecodeError:
            print("Error: --task-config must be a valid JSON string")
        except Exception as e:  # noqa: BLE001
            print(f"Error executing task: {e}")
        return

    if args.list_templates:
        renderer = XMLTemplateRenderer()
        templates = renderer.get_available_templates()
        print("Available XML Templates:")
        for t in templates:
            print(f"  - {t}")
        return

    if args.list_images:
        print("Precompiled Images:")
        print(json.dumps(PRECOMPILED_IMAGES, indent=2))
        print("\nGPU Configuration:")
        print(json.dumps(GPU_CONFIG, indent=2))
        return

    if args.gpu_check:
        print("Running GPU availability check...")
        result = asyncio.run(
            run_gpu_inference(model_type="embeddings", batch_size=1, timeout=30.0)
        )
        print(json.dumps(result, indent=2))
        return

    if args.registry_list:
        print("Listing registry images...")
        result = asyncio.run(sync_registry(action="list"))
        print(json.dumps(result, indent=2))
        return

    if args.run_gpu_inference:
        print(f"Running GPU inference with model: {args.run_gpu_inference}")
        result = asyncio.run(
            run_gpu_inference(model_type=args.run_gpu_inference, batch_size=1)
        )
        print(json.dumps(result, indent=2))
        return

    if args.upsert:
        target, data = args.upsert
        print(f"Upserting: {target}")
        result = asyncio.run(batch_upsert([{"target": target, "data": data}]))
        print(json.dumps(result, indent=2))
        return

    if args.downsert:
        print(f"Downserting: {args.downsert}")
        result = asyncio.run(batch_downsert([args.downsert]))
        print(json.dumps(result, indent=2))
        return

    # Default: show config
    config = SubagentConfig.load()
    perf = config.get("performance_targets", {})
    print("Performance Targets:")
    print(json.dumps(perf, indent=2))
    print("\nPrecompiled Images:")
    print(json.dumps(PRECOMPILED_IMAGES, indent=2))
    print("\nGPU Configuration:")
    print(json.dumps(GPU_CONFIG, indent=2))


if __name__ == "__main__":
    main()
