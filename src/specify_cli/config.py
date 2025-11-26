"""Configuration constants and settings for Specify CLI."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console

console = Console()


class CustomYamlLoader(yaml.SafeLoader):
    """Custom YAML loader that supports !include tag."""

    def __init__(self, stream: Any) -> None:
        self._root = os.getcwd()
        if hasattr(stream, "name"):
            self._root = os.path.split(stream.name)[0]
        super().__init__(stream)

    def include(self, node: Any) -> Any:
        """Include a file referenced by the !include tag."""
        filename = os.path.join(self._root, self.construct_scalar(node))
        with open(filename, encoding="utf-8") as f:
            return yaml.load(f, Loader=CustomYamlLoader)


CustomYamlLoader.add_constructor("!include", CustomYamlLoader.include)


def load_config(config_name: str) -> dict[str, Any]:
    """Load configuration from config directory."""
    # Config is now inside the package: src/specify_cli/config/
    base_path = Path(__file__).parent / "config"
    config_path = base_path / config_name

    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                return yaml.load(f, Loader=CustomYamlLoader) or {}
        except Exception as e:  # pylint: disable=broad-exception-caught
            console.print(
                f"[yellow]Warning: Failed to load {config_name}: {e}[/yellow]"
            )
    return {}


# Load configurations
AGENTS_YAML = load_config("agents.yaml")
if AGENTS_YAML:
    AGENTS_YAML = {k: v for k, v in AGENTS_YAML.items() if not k.startswith("_")}

SETTINGS_YAML = load_config("settings.yaml")
VERSIONS_YAML = load_config("versions.yaml")
COMMANDS_INIT_YAML = load_config("commands/init.yaml")
COMMANDS_CHECK_YAML = load_config("commands/check.yaml")
COMMANDS_VERSION_YAML = load_config("commands/version.yaml")
AGENT_COMMANDS_YAML = load_config("agent_commands.yaml")

# Feature Flags & System Configuration
FEATURES = SETTINGS_YAML.get("features", {})
TELEMETRY_CONFIG = SETTINGS_YAML.get("telemetry", {})
PERFORMANCE_CONFIG = SETTINGS_YAML.get("performance", {})
SECURITY_CONFIG = SETTINGS_YAML.get("security", {})

# Agent configuration with name, folder, install URL, and CLI tool requirement
AGENT_CONFIG = AGENTS_YAML or {}

SCRIPT_TYPE_CHOICES = SETTINGS_YAML.get("script_types", {}) or {
    "sh": "POSIX Shell (bash/zsh)",
    "ps": "PowerShell",
}

BANNER = SETTINGS_YAML.get("cli", {}).get(
    "banner_text",
    "Specify CLI",
)

TAGLINE = SETTINGS_YAML.get("cli", {}).get("tagline", "Spec-Driven Development Toolkit")

_claude_rel_path = SETTINGS_YAML.get("paths", {}).get(
    "claude_local", ".claude/local/claude"
)
CLAUDE_LOCAL_PATH = Path.home() / Path(_claude_rel_path)
