#!/usr/bin/env python3
"""Semantic Kernel CLI Tool.

A minimal Python CLI that leverages YAML configuration for managing
semantic kernel operations, embeddings, and AI workflows.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, cast

import yaml


class SemanticKernelCLI:
    """Main CLI class for Semantic Kernel operations."""

    def __init__(self, config_path: str | None = None) -> None:
        """Initialize the CLI with configuration.

        Args:
            config_path: Optional path to the YAML configuration file.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()

    def _load_config(self, config_path: str | None = None) -> dict[str, Any]:
        """Load YAML configuration file.

        Args:
            config_path: Optional path to the configuration file.

        Returns:
            Configuration dictionary.

        Raises:
            SystemExit: If configuration file is not found or invalid.
        """
        if config_path is None:
            # Default to .config/cli.yml relative to script location
            script_dir = Path(__file__).parent.parent
            config_path = str(script_dir / ".config" / "cli.yml")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return cast(dict[str, Any], config)
        except FileNotFoundError:
            print(f"Error: Configuration file not found: {config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML configuration: {e}")
            sys.exit(1)

    def _setup_logging(self) -> None:
        """Configure logging based on YAML settings."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO").upper())
        log_format = log_config.get("format", "%(levelname)s: %(message)s")

        logging.basicConfig(level=log_level, format=log_format)
        self.logger = logging.getLogger(__name__)

    def get_api_endpoint(self, service: str) -> str:
        """Get API endpoint URL for a specific service.

        Args:
            service: The service name to get the endpoint for.

        Returns:
            The API endpoint URL.
        """
        endpoints = self.config.get("api", {}).get("endpoints", {})
        base_url = self.config["api"]["base_url"]
        return cast(str, endpoints.get(service, base_url))

    def get_openai_config(self) -> dict[str, Any]:
        """Get OpenAI configuration from YAML.

        Returns:
            Dictionary containing OpenAI configuration settings.
        """
        openai_config = self.config.get("openai", {})
        api_key_env = openai_config.get("api_key_env_var", "OPENAI_API_KEY")

        return {
            "api_key": os.getenv(api_key_env),
            "model": openai_config.get("model", "gpt-4"),
            "embedding_model": openai_config.get("embedding_model", "text-embedding-3-small"),
            "max_tokens": openai_config.get("max_tokens", 2000),
            "temperature": openai_config.get("temperature", 0.7),
        }

    def get_database_config(self) -> dict[str, Any]:
        """Get database configuration from YAML.

        Returns:
            Dictionary containing database configuration settings.
        """
        db_config = self.config.get("database", {})
        password_env = db_config.get("password_env_var", "DB_PASSWORD")

        return {
            "host": db_config.get("host", "localhost"),
            "port": db_config.get("port", 5432),
            "database": db_config.get("name", "semantic_kernel"),
            "user": db_config.get("user", "user"),
            "password": os.getenv(password_env),
        }

    def output(self, data: Any, output_format: str | None = None) -> None:
        """Output data in specified format (JSON, YAML, etc.).

        Args:
            data: The data to output.
            output_format: The format to use (json, yaml, etc.).
        """
        output_config = self.config.get("output", {})
        fmt = output_format or output_config.get("default", "json")

        if fmt == "json":
            if output_config.get("pretty_print", True):
                print(json.dumps(data, indent=2))
            else:
                print(json.dumps(data))
        elif fmt == "yaml":
            print(yaml.dump(data, default_flow_style=False))
        else:
            print(data)

    def show_config(self) -> None:
        """Display current configuration."""
        self.logger.info("Current configuration:")
        self.output(self.config, output_format="yaml")

    def list_commands(self) -> None:
        """List all available commands from YAML config."""
        commands = self.config.get("commands", {})
        self.logger.info("Available commands:")

        result = []
        for cmd, details in commands.items():
            result.append(
                {
                    "command": cmd,
                    "description": details.get("description", ""),
                    "subcommands": details.get("subcommands", []),
                }
            )

        self.output(result)

    def get_feature_flags(self) -> dict[str, bool]:
        """Get feature flags from configuration.

        Returns:
            Dictionary of feature flag names to their boolean values.
        """
        return cast(dict[str, bool], self.config.get("features", {}))


def main() -> None:
    """Main entry point for CLI.

    Parses command line arguments and executes the appropriate CLI actions.
    """
    parser = argparse.ArgumentParser(description="Semantic Kernel CLI - Manage AI operations")
    parser.add_argument(
        "--config",
        "-c",
        help="Path to YAML configuration file",
        type=str,
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Display current configuration",
    )
    parser.add_argument(
        "--list-commands",
        action="store_true",
        help="List available commands",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "yaml", "table"],
        help="Output format",
    )

    args = parser.parse_args()

    # Initialize CLI
    cli = SemanticKernelCLI(config_path=args.config)

    # Handle commands
    if args.show_config:
        cli.show_config()
    elif args.list_commands:
        cli.list_commands()
    else:
        # Default: show help
        parser.print_help()
        print("\n--- Configuration Summary ---")
        print(f"API Base URL: {cli.config['api']['base_url']}")
        print(f"Database: {cli.config['database']['name']}")
        print(f"Vector DB: {cli.config['vector_db']['collection']}")
        print(f"Features Enabled: {sum(cli.get_feature_flags().values())}")


if __name__ == "__main__":
    main()
