"""Logging configuration for Specify CLI."""

import logging

from rich.logging import RichHandler


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure structured logging with Rich handler."""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
    )
    return logging.getLogger("specify_cli")


logger = logging.getLogger("specify_cli")
