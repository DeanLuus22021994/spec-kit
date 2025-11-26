#!/usr/bin/env python3
"""
Kantra CLI Runner
Orchestrates Kantra analyze command execution with profile support.
"""
from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ValidationConfig:  # pylint: disable=too-many-instance-attributes
    """Configuration for validation run."""

    input_path: Path
    output_path: Path
    rules_path: Path
    profile: str | None = "recommended"
    label_selector: str | None = None
    run_local: bool = True
    enable_default_rulesets: bool = False
    json_output: bool = True


class KantraRunner:
    """
    Kantra CLI orchestration and execution.

    Responsibilities:
    - Construct Kantra analyze commands
    - Execute validation with proper error handling
    - Parse exit codes and determine status
    - Integrate with cache and reporter
    """

    def __init__(self, workspace_root: Path):
        """
        Initialize Kantra runner.

        Args:
            workspace_root: Root directory of workspace
        """
        self.workspace_root = workspace_root
        self.kantra_binary = self._find_kantra()

    def _find_kantra(self) -> Path:
        """
        Locate Kantra binary.

        Returns:
            Path to kantra executable

        Raises:
            FileNotFoundError: If kantra not found
        """
        # Check PATH
        kantra_path = subprocess.run(["which", "kantra"], capture_output=True, text=True, check=False).stdout.strip()

        if kantra_path:
            return Path(kantra_path)

        # Check common locations
        common_paths = [
            Path("/usr/local/bin/kantra"),
            Path("/usr/bin/kantra"),
            self.workspace_root / "kantra",
        ]

        for path in common_paths:
            if path.exists():
                return path

        raise FileNotFoundError("Kantra CLI not found. Install from: https://github.com/konveyor/kantra")

    def build_command(self, config: ValidationConfig) -> list[str]:
        """
        Build Kantra analyze command from configuration.

        Args:
            config: Validation configuration

        Returns:
            Command as list of arguments
        """
        cmd = [
            str(self.kantra_binary),
            "analyze",
            "--input",
            str(config.input_path),
            "--output",
            str(config.output_path),
            "--rules",
            str(config.rules_path),
            f"--enable-default-rulesets={str(config.enable_default_rulesets).lower()}",
        ]

        if config.run_local:
            cmd.append("--run-local")
        else:
            cmd.append("--run-local=false")

        if config.label_selector:
            cmd.extend(["--label-selector", config.label_selector])

        if config.json_output:
            cmd.append("--json-output")

        return cmd

    def execute(self, config: ValidationConfig) -> dict[str, Any]:
        """
        Execute Kantra validation.

        Args:
            config: Validation configuration

        Returns:
            Execution result with status, exit_code, stdout, stderr
        """
        cmd = self.build_command(config)

        logger.info("Executing Kantra: %s", " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                check=False,  # Don't raise on non-zero exit
            )

            # Interpret exit codes
            # 0 = success, 1 = mandatory violations, 2 = optional issues
            status = self._interpret_exit_code(result.returncode)

            return {
                "status": status,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": cmd,
            }

        except (OSError, subprocess.SubprocessError) as e:
            logger.error("Kantra execution failed: %s", e)
            return {
                "status": "error",
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "command": cmd,
            }

    def _interpret_exit_code(self, exit_code: int) -> str:
        """
        Interpret Kantra exit code.

        Args:
            exit_code: Process exit code

        Returns:
            Status string (success, mandatory_violations, optional_issues, error)
        """
        if not exit_code:
            return "success"
        if exit_code == 1:
            return "mandatory_violations"
        if exit_code == 2:
            return "optional_issues"
        return "error"

    def validate_repository(self, profile: str = "recommended", label_selector: str | None = None) -> dict[str, Any]:
        """
        Validate entire repository with profile.

        Args:
            profile: Validation profile name
            label_selector: Custom label selector (overrides profile)

        Returns:
            Validation result
        """
        config = ValidationConfig(
            input_path=self.workspace_root,
            output_path=self.workspace_root / "tools/.config/validation/reports/latest",
            rules_path=self.workspace_root / "tools/.config/validation/rules",
            profile=profile,
            label_selector=label_selector,
        )

        # Create output directory
        config.output_path.mkdir(parents=True, exist_ok=True)

        return self.execute(config)

    def validate_file(self, file_path: Path, profile: str = "recommended") -> dict[str, Any]:
        """
        Validate single file.

        Args:
            file_path: Path to YAML file
            profile: Validation profile

        Returns:
            Validation result
        """
        config = ValidationConfig(
            input_path=file_path,
            output_path=self.workspace_root / "tools/.config/validation/reports/latest",
            rules_path=self.workspace_root / "tools/.config/validation/rules",
            profile=profile,
        )

        config.output_path.mkdir(parents=True, exist_ok=True)

        return self.execute(config)
