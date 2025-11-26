#!/usr/bin/env python3
"""Run Command.

Execute YAML validation on files and directories.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

try:
    from watchdog.events import FileSystemEventHandler as WatchdogHandler  # type: ignore[import-untyped]
    from watchdog.observers import Observer  # type: ignore[import-untyped]

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    WatchdogHandler = None  # type: ignore[assignment,misc]
    Observer = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)


def _create_file_handler(callback: Callable[[str], None]) -> Any:
    """Create a file system event handler for watch mode."""
    if not WATCHDOG_AVAILABLE or WatchdogHandler is None:
        raise RuntimeError("watchdog package not available")

    class ValidationFileHandler(WatchdogHandler):  # type: ignore[misc]
        """File system event handler for watch mode."""

        def __init__(self) -> None:
            super().__init__()
            self.last_modified: dict[str, float] = {}

        def on_modified(self, event: Any) -> None:
            """Handle file modification events."""
            if event.is_directory:
                return

            if not event.src_path.endswith((".yaml", ".yml")):
                return

            # Debounce rapid file changes
            now = time.time()
            if event.src_path in self.last_modified:
                if now - self.last_modified[event.src_path] < 1.0:
                    return

            self.last_modified[event.src_path] = now
            callback(event.src_path)

    return ValidationFileHandler()


def run_validation(
    profile: str,
    input_path: Path,
    output_path: Path | None,
    output_format: str,
    fail_on_error: bool,
    fail_on_warning: bool,
    watch: bool,
    verbose: bool,
) -> int:
    """Run YAML validation.

    Args:
        profile: Validation profile name.
        input_path: Input directory or file.
        output_path: Output file path.
        output_format: Output format.
        fail_on_error: Exit with error code on errors.
        fail_on_warning: Exit with error code on warnings.
        watch: Watch for changes.
        verbose: Verbose output.

    Returns:
        Exit code.
    """
    logger.info("Running validation with profile: %s", profile)
    logger.info("Input: %s", input_path)

    if watch:
        if not WATCHDOG_AVAILABLE:
            logger.error("Watch mode requires watchdog package. Install with: pip install watchdog")
            return 1
        return run_watch_mode(input_path, profile, output_format, verbose)

    # Run validation once
    return run_single_validation(input_path, profile, output_path, output_format, fail_on_error, fail_on_warning, verbose)


def run_single_validation(
    input_path: Path,
    profile: str,
    output_path: Path | None,
    output_format: str,
    fail_on_error: bool,
    fail_on_warning: bool,
    verbose: bool,  # pylint: disable=unused-argument
) -> int:
    """Run validation once.

    Args:
        input_path: Path to input file or directory.
        profile: Validation profile name.
        output_path: Optional path for output file.
        output_format: Format for output (text, json, etc.).
        fail_on_error: Whether to fail on validation errors.
        fail_on_warning: Whether to fail on validation warnings.
        verbose: Enable verbose output.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    try:
        # Build validation command
        cmd = ["python", "-m", "core.cli", "validate", "--mode", profile, "--format", output_format]

        if output_path:
            cmd.extend(["--output", str(output_path)])

        if fail_on_warning:
            cmd.append("--fail-on-warning")

        # Run validation
        result = subprocess.run(
            cmd,
            cwd=input_path if input_path.is_dir() else input_path.parent,
            capture_output=True,
            text=True,
            check=False,
        )

        # Print output
        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print(result.stderr, file=sys.stderr)

        # Parse results
        if output_format == "json" and result.stdout:
            try:
                results = json.loads(result.stdout)
                error_count = results.get("errors", 0)
                warning_count = results.get("warnings", 0)

                logger.info("Validation complete: %d errors, %d warnings", error_count, warning_count)

                if fail_on_error and error_count > 0:
                    return 1
                if fail_on_warning and warning_count > 0:
                    return 1

            except json.JSONDecodeError:
                logger.error("Failed to parse validation results")
                return 1

        return result.returncode

    except subprocess.SubprocessError as e:
        logger.error("Validation failed: %s", e)
        return 1


def run_watch_mode(input_path: Path, profile: str, output_format: str, verbose: bool) -> int:
    """Run validation in watch mode."""
    if not WATCHDOG_AVAILABLE or Observer is None:
        logger.error("Watch mode requires watchdog package. Install with: pip install watchdog")
        return 1

    logger.info("Starting watch mode...")
    logger.info("Watching: %s", input_path)
    logger.info("Press Ctrl+C to stop")

    def on_file_change(file_path: str) -> None:
        """Handle file change event."""
        logger.info("File changed: %s", file_path)
        run_single_validation(Path(file_path), profile, None, output_format, False, False, verbose)

    # Set up file watcher
    event_handler = _create_file_handler(on_file_change)
    observer = Observer()
    observer.schedule(event_handler, str(input_path), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping watch mode...")
        observer.stop()

    observer.join()
    return 0
