"""Main entry point for Specify CLI."""

from __future__ import annotations

import typer

from specify_cli.commands.check import check
from specify_cli.commands.init import init
from specify_cli.commands.version import version

app = typer.Typer(
    name="specify",
    help="Specify CLI - Spec-Driven Development Toolkit",
    add_completion=False,
)

app.command()(init)
app.command()(check)
app.command()(version)


def main() -> None:
    """Execute the CLI application."""
    app()


if __name__ == "__main__":
    main()
