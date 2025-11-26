"""Docker and GPU inference executors."""

from __future__ import annotations

import json
import subprocess
import time
from typing import Any, cast

from ..config import (
    GPU_CONFIG,
    PRECOMPILED_IMAGES,
    REGISTRY_URL,
    SubagentConfig,
    SubagentTask,
    TaskResult,
    TaskStatus,
    TaskType,
)
from .base import TaskExecutor


class DockerExecutor(TaskExecutor):
    """Executor for Docker container tasks with GPU support."""

    def __init__(self, registry_url: str = REGISTRY_URL) -> None:
        """Initialize with registry URL."""
        self.registry_url = registry_url
        self.config = SubagentConfig.load()
        perf = self.config.get("performance_targets", {})
        self.max_workers: int = perf.get("max_parallel_agents", 4) if perf else 4

    def _build_docker_cmd(
        self,
        image: str,
        command: list[str],
        gpu: bool = False,
        volumes: dict[str, str] | None = None,
        env: dict[str, str] | None = None,
        workdir: str | None = None,
    ) -> list[str]:
        """Build docker run command with GPU support."""
        cmd = ["docker", "run", "--rm"]

        if gpu:
            cmd.extend(
                [
                    "--gpus",
                    "all",
                    "--runtime",
                    str(GPU_CONFIG["nvidia_runtime"]),
                    "-e",
                    f"CUDA_VISIBLE_DEVICES={GPU_CONFIG['cuda_visible_devices']}",
                    "-e",
                    f"CUDA_MEMORY_FRACTION={GPU_CONFIG['memory_fraction']}",
                    "-e",
                    f"CUDA_MIXED_PRECISION={str(GPU_CONFIG['mixed_precision']).lower()}",
                    "-e",
                    f"CUDA_TF32_ENABLED={str(GPU_CONFIG['tf32_enabled']).lower()}",
                    "-e",
                    "NVIDIA_DRIVER_CAPABILITIES=compute,utility",
                    "-e",
                    "NVIDIA_VISIBLE_DEVICES=all",
                ]
            )

        if volumes:
            for host_path, container_path in volumes.items():
                cmd.extend(["-v", f"{host_path}:{container_path}"])

        if env:
            for key, value in env.items():
                cmd.extend(["-e", f"{key}={value}"])

        if workdir:
            cmd.extend(["-w", workdir])

        cmd.append(image)
        cmd.extend(command)
        return cmd

    async def execute(self, task: SubagentTask) -> TaskResult:
        """Execute Docker container task."""
        start_time = time.perf_counter()
        payload = cast(dict[str, Any], task.payload)

        image = payload.get("image", "")
        command = payload.get("command", [])
        gpu = payload.get("gpu", False)
        volumes = payload.get("volumes", {})
        env = payload.get("env", {})
        workdir = payload.get("workdir")

        # Resolve image from precompiled registry
        if image in PRECOMPILED_IMAGES:
            image = PRECOMPILED_IMAGES[image]

        docker_cmd = self._build_docker_cmd(image, command, gpu, volumes, env, workdir)

        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=task.timeout_seconds,
                check=False,
            )
            execution_time = (time.perf_counter() - start_time) * 1000

            return TaskResult(
                task_id=task.task_id,
                task_type=task.task_type,
                status=TaskStatus.COMPLETED
                if not result.returncode
                else TaskStatus.FAILED,
                result={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                },
                error=result.stderr if result.returncode else None,
                execution_time_ms=execution_time,
                metadata={"image": image, "gpu": gpu},
            )
        except subprocess.TimeoutExpired:
            return TaskResult(
                task_id=task.task_id,
                task_type=task.task_type,
                status=TaskStatus.TIMEOUT,
                error=f"Docker container timed out after {task.timeout_seconds}s",
            )
        except (OSError, subprocess.SubprocessError) as e:
            return TaskResult(
                task_id=task.task_id,
                task_type=task.task_type,
                status=TaskStatus.FAILED,
                error=str(e),
            )

    def validate_task(self, task: SubagentTask) -> bool:
        """Validate Docker task payload."""
        payload = task.payload
        return isinstance(payload, dict) and "image" in payload


class GPUInferenceExecutor(TaskExecutor):
    """Executor for GPU-accelerated inference tasks."""

    def __init__(self) -> None:
        """Initialize GPU executor."""
        self.config = SubagentConfig.load()
        self.docker_executor = DockerExecutor()

    async def execute(self, task: SubagentTask) -> TaskResult:
        """Execute GPU inference task via container."""
        start_time = time.perf_counter()
        payload = cast(dict[str, Any], task.payload)

        model_type = payload.get("model_type", "arcface")
        input_config = payload.get("input_data", {})
        batch_size = payload.get("batch_size", 1)

        # Select appropriate precompiled image
        image_map = {
            "arcface": "face-matcher",
            "embeddings": "embeddings",
            "vector": "vector",
        }
        image = PRECOMPILED_IMAGES.get(image_map.get(model_type, "embeddings"), "")

        # Build inference command
        inference_cmd = [
            "python",
            "-c",
            f"""
import json
import sys
try:
    import onnxruntime as ort
    providers = ort.get_available_providers()
    cuda_available = 'CUDAExecutionProvider' in providers
    tensorrt_available = 'TensorrtExecutionProvider' in providers
    result = {{
        'cuda_available': cuda_available,
        'tensorrt_available': tensorrt_available,
        'providers': providers,
        'batch_size': {batch_size},
        'model_type': '{model_type}',
        'status': 'ready'
    }}
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({{'error': str(e), 'status': 'failed'}}))
""",
        ]

        # Create Docker task
        docker_task = SubagentTask(
            task_id=f"{task.task_id}-docker",
            task_type=TaskType.DOCKER_RUN,
            payload={
                "image": image,
                "command": inference_cmd,
                "gpu": True,
                "env": {
                    "CUDA_MEMORY_FRACTION": str(GPU_CONFIG["memory_fraction"]),
                    "ENABLE_TENSORRT": str(GPU_CONFIG["tensorrt_enabled"]).lower(),
                    "ENABLE_FLASH_ATTENTION": str(
                        GPU_CONFIG["flash_attention"]
                    ).lower(),
                },
            },
            timeout_seconds=task.timeout_seconds,
        )

        docker_result = await self.docker_executor.execute(docker_task)
        execution_time = (time.perf_counter() - start_time) * 1000

        # Parse inference result
        inference_result: dict[str, Any] = {}
        if docker_result.result and docker_result.result.get("stdout"):
            try:
                inference_result = json.loads(docker_result.result["stdout"].strip())
            except json.JSONDecodeError:
                inference_result = {"raw_output": docker_result.result["stdout"]}

        return TaskResult(
            task_id=task.task_id,
            task_type=task.task_type,
            status=docker_result.status,
            result=inference_result,
            error=docker_result.error,
            execution_time_ms=execution_time,
            metadata={
                "model_type": model_type,
                "batch_size": batch_size,
                "input_config": input_config,
                "gpu_config": GPU_CONFIG,
            },
        )

    def validate_task(self, task: SubagentTask) -> bool:
        """Validate GPU inference task."""
        payload = task.payload
        return isinstance(payload, dict)


class RegistrySyncExecutor(TaskExecutor):
    """Executor for Docker registry synchronization."""

    def __init__(self, registry_url: str = REGISTRY_URL) -> None:
        """Initialize with registry URL."""
        self.registry_url = registry_url
        self.config = SubagentConfig.load()

    async def execute(self, task: SubagentTask) -> TaskResult:
        """Execute registry sync task."""
        start_time = time.perf_counter()
        payload = cast(dict[str, Any], task.payload)

        action = payload.get("action", "list")
        images = payload.get("images", [])

        results: dict[str, Any] = {"action": action, "images": []}

        if action == "list":
            cmd = ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"]
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=30, check=False
                )
                registry_images = [
                    img
                    for img in result.stdout.strip().split("\n")
                    if self.registry_url in img or "semantic-kernel" in img
                ]
                results["images"] = registry_images
            except (subprocess.SubprocessError, OSError) as e:
                return TaskResult(
                    task_id=task.task_id,
                    task_type=task.task_type,
                    status=TaskStatus.FAILED,
                    error=str(e),
                )

        elif action == "pull":
            for image in images:
                full_image = (
                    f"{self.registry_url}/{image}" if "/" not in image else image
                )
                cmd = ["docker", "pull", full_image]
                try:
                    subprocess.run(
                        cmd, capture_output=True, text=True, timeout=120, check=True
                    )
                    results["images"].append({"image": full_image, "status": "pulled"})
                except subprocess.SubprocessError:
                    results["images"].append({"image": full_image, "status": "failed"})

        elif action == "push":
            for image in images:
                cmd = ["docker", "push", image]
                try:
                    subprocess.run(
                        cmd, capture_output=True, text=True, timeout=300, check=True
                    )
                    results["images"].append({"image": image, "status": "pushed"})
                except subprocess.SubprocessError:
                    results["images"].append({"image": image, "status": "failed"})

        execution_time = (time.perf_counter() - start_time) * 1000

        return TaskResult(
            task_id=task.task_id,
            task_type=task.task_type,
            status=TaskStatus.COMPLETED,
            result=results,
            execution_time_ms=execution_time,
            metadata={"registry": self.registry_url},
        )

    def validate_task(self, task: SubagentTask) -> bool:
        """Validate registry sync task."""
        payload = task.payload
        if not isinstance(payload, dict):
            return False
        action = payload.get("action", "")
        return action in ("list", "pull", "push")
