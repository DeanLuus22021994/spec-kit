from __future__ import annotations

import importlib.metadata

from rich.console import Console

from specify_cli.ui import show_banner

console = Console()


def version():
    """Show version information."""
    show_banner()
    try:
        ver = importlib.metadata.version("specify-cli")
    except importlib.metadata.PackageNotFoundError:
        ver = "unknown"
    console.print(f"Specify CLI version: [bold cyan]{ver}[/bold cyan]")
