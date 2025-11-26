#!/usr/bin/env python3
"""Custom Provider Integration.

Extends Kantra with custom providers for specialized validation.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """Base class for custom validation providers."""

    def __init__(self, name: str, version: str) -> None:
        """Initialize provider.

        Args:
            name: Provider name.
            version: Provider version.
        """
        self.name = name
        self.version = version

    @abstractmethod
    def validate(self, content: str, file_path: Path) -> list[dict[str, Any]]:
        """Validate file content.

        Args:
            content: File content.
            file_path: Path to file.

        Returns:
            List of validation issues.
        """

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """Get provider capabilities.

        Returns:
            List of capability names.
        """


class YAMLStructureProvider(BaseProvider):
    """Provider for YAML structure validation."""

    def __init__(self) -> None:
        """Initialize YAML structure provider."""
        super().__init__("yaml-structure", "1.0.0")

    def validate(self, content: str, file_path: Path) -> list[dict[str, Any]]:
        """Validate YAML structure.

        Args:
            content: File content.
            file_path: Path to file.

        Returns:
            List of validation issues.
        """
        issues: list[dict[str, Any]] = []

        try:
            # Parse YAML
            data = yaml.safe_load(content)

            # Check for metadata block
            if isinstance(data, dict):
                if "metadata" not in data:
                    issues.append(
                        {
                            "ruleID": "custom-metadata-missing",
                            "severity": "mandatory",
                            "message": "Missing metadata block",
                            "file": str(file_path),
                            "line": 1,
                        }
                    )

                # Check for version field
                if "version" not in data:
                    issues.append(
                        {
                            "ruleID": "custom-version-missing",
                            "severity": "mandatory",
                            "message": "Missing version field",
                            "file": str(file_path),
                            "line": 1,
                        }
                    )

        except yaml.YAMLError as e:
            issues.append(
                {
                    "ruleID": "custom-yaml-parse-error",
                    "severity": "error",
                    "message": f"YAML parse error: {e}",
                    "file": str(file_path),
                    "line": getattr(e, "problem_mark", {}).get("line", 1),
                }
            )

        return issues

    def get_capabilities(self) -> list[str]:
        """Get provider capabilities.

        Returns:
            List of capability names.
        """
        return ["structure-validation", "metadata-validation", "syntax-validation"]


class CustomProvider:
    """Custom provider registry and orchestration.

    Manages custom providers and integrates them with Kantra workflow.
    """

    def __init__(self) -> None:
        """Initialize provider registry."""
        self.providers: dict[str, BaseProvider] = {}
        self._register_default_providers()

    def _register_default_providers(self) -> None:
        """Register default providers."""
        self.register(YAMLStructureProvider())

    def register(self, provider: BaseProvider) -> None:
        """Register custom provider.

        Args:
            provider: Provider instance.
        """
        logger.info("Registering provider: %s v%s", provider.name, provider.version)
        self.providers[provider.name] = provider

    def unregister(self, name: str) -> None:
        """Unregister provider.

        Args:
            name: Provider name.
        """
        if name in self.providers:
            del self.providers[name]
            logger.info("Unregistered provider: %s", name)

    def get_provider(self, name: str) -> BaseProvider | None:
        """Get provider by name.

        Args:
            name: Provider name.

        Returns:
            Provider instance or None.
        """
        return self.providers.get(name)

    def list_providers(self) -> list[dict[str, Any]]:
        """List all registered providers.

        Returns:
            List of provider metadata.
        """
        return [
            {
                "name": p.name,
                "version": p.version,
                "capabilities": p.get_capabilities(),
            }
            for p in self.providers.values()
        ]

    def validate_with_providers(
        self,
        file_path: Path,
        provider_names: list[str] | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """Validate file with custom providers.

        Args:
            file_path: Path to file.
            provider_names: List of provider names (None = all).

        Returns:
            Dictionary of provider results.

        Raises:
            FileNotFoundError: If file does not exist.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = file_path.read_text(encoding="utf-8")

        # Select providers
        if provider_names:
            providers = [self.providers[name] for name in provider_names if name in self.providers]
        else:
            providers = list(self.providers.values())

        # Run validation
        results: dict[str, list[dict[str, Any]]] = {}
        for provider in providers:
            try:
                issues = provider.validate(content, file_path)
                results[provider.name] = issues
                logger.info("Provider %s: %s issues found", provider.name, len(issues))
            except (OSError, ValueError, yaml.YAMLError) as e:
                logger.error("Provider %s failed: %s", provider.name, e)
                results[provider.name] = [
                    {
                        "ruleID": "provider-error",
                        "severity": "error",
                        "message": f"Provider error: {e}",
                        "file": str(file_path),
                    }
                ]

        return results
