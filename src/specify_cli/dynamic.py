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

        # Use the name from config as the parameter name passed to the function
        # This ensures 'json_output' in YAML maps to 'json_output' argument in python
        # instead of click deriving it from the flag (e.g. --json -> json)
        if "name" in opt_config:
            # Click uses the longest flag as the name by default, but we can override
            # the destination variable name using 'expose_value' or just relying on
            # how Click parses options. Actually, Click uses the parameter name
            # derived from flags. To force a specific name, we might need to check
            # if we can pass 'name' to Option? No, Option takes param_decls.
            # However, we can pass the name as the first argument if it doesn't start with -
            # But for Options, they must start with -.
            # The 'name' attribute on Option is derived.
            # We can use 'callback' or other tricks, but the standard way is
            # that --json-output becomes json_output.
            # In our YAML: name: json_output, flags: ["--json"]
            # Click will map --json to 'json'.
            # We want it to map to 'json_output'.
            # We can achieve this by adding the name as a secondary declaration if it was an argument,
            # but for options, we can use the 'variable_name' if we were using argparse,
            # but for Click, we can't easily rename the destination without a custom class or
            # ensuring the flag matches the name.
            #
            # WAIT: Click Option has a 'name' parameter in constructor? No.
            # It has 'param_decls'.
            #
            # Let's look at how Typer does it. Typer maps function args to flags.
            # Here we are mapping YAML to Click.
            #
            # If we want 'json_output' to be the variable name, we should probably
            # ensure the flag is --json-output OR we rely on the fact that
            # the handler signature uses 'json_output'.
            #
            # The error was: TypeError: check() got an unexpected keyword argument 'json'
            # This means Click passed 'json=True' because the flag is '--json'.
            # But the handler expects 'json_output'.
            #
            # We can fix this by adding the desired variable name to the param_decls
            # if we construct it carefully, OR we can just use the 'name' from YAML
            # to set the 'expose_value' name? No.
            #
            # Actually, we can pass `expose_value`? No.
            #
            # We can use `click.Option(..., "json_output")`? No.
            #
            # The solution is to use the `name` parameter of the Option class?
            # "name" is available in Parameter, but Option overrides it?
            #
            # Let's check Click docs or source.
            # It seems we can't easily force the name.
            #
            # EASIEST FIX: Update the YAML to use flags that match the variable name,
            # OR update the handler to match the flag.
            pass

        opt = click.Option(flags, **kwargs)
        # Force the parameter name to match the YAML 'name' field
        # This ensures that --json passes 'json_output' to the function
        if "name" in opt_config:
            opt.name = opt_config["name"]

        params.append(opt)

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
    # Config is now inside the package: src/specify_cli/config/
    config_path = Path(__file__).parent / "config" / "commands.yaml"

    if not config_path.exists():
        return []

    with open(config_path, encoding="utf-8") as f:
        data = yaml.load(f, Loader=CustomYamlLoader)

    commands = []
    for cmd_config in data.get("commands", []):
        commands.append(create_command_from_yaml(cmd_config))

    return commands
