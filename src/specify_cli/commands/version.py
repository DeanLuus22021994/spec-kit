"""Version command handler."""

from __future__ import annotations

import importlib.metadata

from rich.console import Console

from specify_cli.config import COMMANDS_VERSION_YAML
from specify_cli.ui import show_banner

console = Console()


def version() -> None:
    """Show version information."""
    show_banner()
    try:
        ver = importlib.metadata.version("specify-cli")
    except importlib.metadata.PackageNotFoundError:
        ver = "unknown"

    output_format = COMMANDS_VERSION_YAML.get("messages", {}).get(
        "output_format", "Specify CLI version: [bold cyan]{version}[/bold cyan]"
    )
    console.print(output_format.format(version=ver))
