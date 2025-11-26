"""Utility functions for Specify CLI."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

from specify_cli.config import CLAUDE_LOCAL_PATH, TELEMETRY_CONFIG

if TYPE_CHECKING:
    from specify_cli.ui import StepTracker

console = Console()


class TelemetryClient:
    """Client for sending telemetry data."""

    def __init__(self) -> None:
        self.enabled = TELEMETRY_CONFIG.get("enabled", False)
        self.service_name = TELEMETRY_CONFIG.get("service_name", "specify-cli")
        self.endpoint = TELEMETRY_CONFIG.get("endpoint")

    def track_event(self, event_name: str, properties: dict | None = None) -> None:
        """Track a usage event."""
        if not self.enabled:
            return
        # Placeholder for actual OTel implementation
        # In a real scenario, this would send data to the collector
        pass

    def track_exception(self, exception: Exception) -> None:
        """Track an exception."""
        if not self.enabled:
            return
        pass


telemetry = TelemetryClient()


def run_command(
    cmd: list[str],
    check_return: bool = True,
    capture: bool = False,
    shell: bool = False,
) -> str | None:
    """Run a shell command and optionally capture output."""
    try:
        if capture:
            result = subprocess.run(
                cmd, check=check_return, capture_output=True, text=True, shell=shell
            )
            return result.stdout.strip()
        else:
            subprocess.run(cmd, check=check_return, shell=shell)
            return None
    except subprocess.CalledProcessError as e:
        if check_return:
            console.print(f"[red]Error running command:[/red] {' '.join(cmd)}")
            console.print(f"[red]Exit code:[/red] {e.returncode}")
            if hasattr(e, "stderr") and e.stderr:
                console.print(f"[red]Error output:[/red] {e.stderr}")
            raise
        return None


def check_tool(tool: str, tracker: StepTracker | None = None) -> str | None:
    """Check if a tool is installed. Optionally update tracker.

    Args:
        tool: Name of the tool to check
        tracker: Optional StepTracker to update with results

    Returns:
        Path to the tool if found, None otherwise
    """
    # Special handling for Claude CLI after `claude migrate-installer`
    # See: https://github.com/github/spec-kit/issues/123
    # The migrate-installer command REMOVES the original executable from PATH
    # and creates an alias at ~/.claude/local/claude instead
    # This path should be prioritized over other claude executables in PATH
    if tool == "claude":
        if CLAUDE_LOCAL_PATH.exists() and CLAUDE_LOCAL_PATH.is_file():
            if tracker:
                tracker.complete(tool, "available")
            return str(CLAUDE_LOCAL_PATH)

    found_path = shutil.which(tool)

    if tracker:
        if found_path:
            tracker.complete(tool, "available")
        else:
            tracker.error(tool, "not found")

    return found_path


def merge_json_files(
    existing_path: Path, new_content: dict, verbose: bool = False
) -> dict:
    """Merge new JSON content into existing JSON file.

    Performs a deep merge where:
    - New keys are added
    - Existing keys are preserved unless overwritten by new content
    - Nested dictionaries are merged recursively
    - Lists and other values are replaced (not merged)

    Args:
        existing_path: Path to existing JSON file
        new_content: New JSON content to merge in
        verbose: Whether to print merge details

    Returns:
        Merged JSON content as dict
    """
    try:
        with open(existing_path, encoding="utf-8") as f:
            existing_content = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist or is invalid, just use new content
        return new_content

    def deep_merge(base: dict, update: dict) -> dict:
        """Recursively merge update dict into base dict."""
        result = base.copy()
        for key, value in update.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                # Recursively merge nested dictionaries
                result[key] = deep_merge(result[key], value)
            else:
                # Add new key or replace existing value
                result[key] = value
        return result

    merged = deep_merge(existing_content, new_content)

    if verbose:
        console.print(f"[cyan]Merged JSON file:[/cyan] {existing_path.name}")

    return merged


def handle_vscode_settings(
    sub_item: Path,
    dest_file: Path,
    rel_path: Path,
    verbose: bool = False,
    tracker: StepTracker | None = None,
) -> None:
    """Handle merging or copying of .vscode/settings.json files."""

    def log(message: str, color: str = "green") -> None:
        if verbose and not tracker:
            console.print(f"[{color}]{message}[/] {rel_path}")

    try:
        with open(sub_item, encoding="utf-8") as f:
            new_settings = json.load(f)

        if dest_file.exists():
            merged = merge_json_files(
                dest_file, new_settings, verbose=verbose and not tracker
            )
            with open(dest_file, "w", encoding="utf-8") as f:
                json.dump(merged, f, indent=4)
                f.write("\n")
            log("Merged:", "green")
        else:
            shutil.copy2(sub_item, dest_file)
            log("Copied (no existing settings.json):", "blue")

    except Exception as e:  # pylint: disable=broad-except
        log(f"Warning: Could not merge, copying instead: {e}", "yellow")
        shutil.copy2(sub_item, dest_file)
