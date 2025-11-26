"""Main entry point for Specify CLI."""

from __future__ import annotations

from typing import cast

import click
import typer

from specify_cli.dynamic import load_commands
from specify_cli.utils import telemetry

app = typer.Typer(
    name="specify",
    help="Specify CLI - Spec-Driven Development Toolkit",
    add_completion=False,
)


@app.callback()
def callback() -> None:
    """Specify CLI - Spec-Driven Development Toolkit"""


def main() -> None:
    """Execute the CLI application."""
    telemetry.track_event("cli_start")

    # Convert Typer app to Click Group
    cli = cast(click.Group, typer.main.get_command(app))

    # Load and register dynamic commands
    for cmd in load_commands():
        cli.add_command(cmd)

    # Run the Click CLI
    cli()


if __name__ == "__main__":
    main()
