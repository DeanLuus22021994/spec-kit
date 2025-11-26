"""Dynamic command loading from YAML configuration."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import click
import yaml

from specify_cli.config import CustomYamlLoader


def load_handler(handler_path: str) -> Callable:
    """Load a function from a string path like 'module.path:function_name'."""
    module_name, func_name = handler_path.split(":")
    module = importlib.import_module(module_name)
    return cast(Callable, getattr(module, func_name))


def create_command_from_yaml(config: dict[str, Any]) -> click.Command:
    """Create a Click command from a dictionary configuration."""
    handler = load_handler(config["handler"])

    params: list[click.Parameter] = []

    # Process Arguments
    for arg_config in config.get("arguments", []):
        # Click arguments are positional
        # required defaults to True in Click
        required = arg_config.get("required", True)

        # Note: Click arguments don't support 'help' in the standard help output
        # unlike Options. Typer adds this via extended help formatting.
        # For now, we stick to standard Click behavior.
        params.append(
            click.Argument(
                [arg_config["name"]],
                required=required,
            )
        )

    # Process Options
    for opt_config in config.get("options", []):
        flags = opt_config["flags"]
        kwargs = {
            "help": opt_config.get("help"),
            "is_flag": opt_config.get("type") == "boolean",
        }

        if opt_config.get("type") == "string":
            kwargs["type"] = click.STRING
        elif opt_config.get("type") == "boolean":
            kwargs["type"] = click.BOOL

        params.append(click.Option(flags, **kwargs))

    help_text = config.get("description", config.get("help"))
    short_help = config.get("help")

    return click.Command(
        name=config["name"],
        callback=handler,
        params=params,
        help=help_text,
        short_help=short_help,
    )


def load_commands() -> list[click.Command]:
    """Load all commands defined in the YAML configuration."""
    # src/specify_cli/dynamic.py -> src/specify_cli -> src -> root
    config_path = Path(__file__).parent.parent.parent / ".config" / "commands.yaml"

    if not config_path.exists():
        return []

    with open(config_path, encoding="utf-8") as f:
        data = yaml.load(f, Loader=CustomYamlLoader)

    commands = []
    for cmd_config in data.get("commands", []):
        commands.append(create_command_from_yaml(cmd_config))

    return commands
