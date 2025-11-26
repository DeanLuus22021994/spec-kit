#!/usr/bin/env python3
"""
Rule Registry
Auto-discover and load validation rules from modular packages.
"""
from __future__ import annotations

import logging
from pathlib import Path
from types import ModuleType
from typing import Any

_yaml: ModuleType | None
try:
    import yaml as _yaml_module

    _yaml = _yaml_module
except ImportError:
    _yaml = None

logger = logging.getLogger(__name__)


class RuleRegistry:
    """
    Rule discovery and loading from modular packages.

    Scans rules/ directory for packages and loads their rulesets.
    Maintains catalog of all available rules and their metadata.
    """

    def __init__(self, rules_root: Path):
        """
        Initialize rule registry.

        Args:
            rules_root: Root directory containing rule packages
        """
        if not _yaml:
            raise ImportError("PyYAML required for rule registry")

        self.rules_root = rules_root
        self.packages: dict[str, dict[str, Any]] = {}
        self.rules: dict[str, dict[str, Any]] = {}

    def discover_packages(self) -> list[str]:
        """
        Discover rule packages.

        Returns:
            List of package names
        """
        if not self.rules_root.exists():
            logger.warning("Rules directory not found: %s", self.rules_root)
            return []

        packages = []
        for item in self.rules_root.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                # Check for ruleset.yaml
                ruleset_path = item / "ruleset.yaml"
                if ruleset_path.exists():
                    packages.append(item.name)
                    logger.debug("Discovered package: %s", item.name)

        return sorted(packages)

    def load_package(self, package_name: str) -> dict[str, Any]:
        """
        Load rule package metadata.

        Args:
            package_name: Package name

        Returns:
            Package metadata
        """
        package_dir = self.rules_root / package_name
        ruleset_path = package_dir / "ruleset.yaml"

        if not ruleset_path.exists():
            raise FileNotFoundError(f"Ruleset not found: {ruleset_path}")

        with open(ruleset_path, "r", encoding="utf-8") as f:
            ruleset: dict[str, Any] = (_yaml.safe_load(f) if _yaml else None) or {}

        # Load rule files referenced in ruleset
        rule_files: list[str] = []
        for rule_file in package_dir.glob("*.yaml"):
            if rule_file.name != "ruleset.yaml":
                rule_files.append(rule_file.name)

        metadata = ruleset.get("metadata", {})
        package_metadata: dict[str, Any] = {
            "name": package_name,
            "version": metadata.get("version", "unknown") if metadata else "unknown",
            "description": metadata.get("description", "") if metadata else "",
            "ruleset": ruleset,
            "rule_files": rule_files,
            "path": package_dir,
        }

        self.packages[package_name] = package_metadata
        logger.info("Loaded package: %s v%s", package_name, package_metadata["version"])

        return package_metadata

    def load_all_packages(self) -> None:
        """Load all discovered packages."""
        packages = self.discover_packages()
        for package_name in packages:
            try:
                self.load_package(package_name)
            except (OSError, ValueError, KeyError) as e:
                logger.error("Failed to load package %s: %s", package_name, e)

    def get_package(self, package_name: str) -> dict[str, Any] | None:
        """
        Get loaded package metadata.

        Args:
            package_name: Package name

        Returns:
            Package metadata or None
        """
        return self.packages.get(package_name)

    def list_packages(self) -> list[dict[str, Any]]:
        """
        List all loaded packages.

        Returns:
            List of package metadata
        """
        return [
            {
                "name": pkg["name"],
                "version": pkg["version"],
                "description": pkg["description"],
                "rule_count": len(pkg["rule_files"]),
            }
            for pkg in self.packages.values()
        ]

    def extract_rules(self, package_name: str) -> list[dict[str, Any]]:
        """
        Extract individual rules from package.

        Args:
            package_name: Package name

        Returns:
            List of rule definitions
        """
        package = self.get_package(package_name)
        if not package:
            raise ValueError(f"Package not loaded: {package_name}")

        rules: list[dict[str, Any]] = []
        package_dir = package["path"]

        for rule_file in package["rule_files"]:
            rule_path = package_dir / rule_file

            try:
                with open(rule_path, "r", encoding="utf-8") as f:
                    content = _yaml.safe_load(f) if _yaml else None

                # Extract rules from content
                if isinstance(content, list):
                    rules.extend(content)
                elif isinstance(content, dict):
                    # Check for rules key
                    if "rules" in content:
                        rules.extend(content["rules"])
                    else:
                        rules.append(content)

            except (OSError, ValueError, KeyError) as e:
                logger.error("Failed to extract rules from %s: %s", rule_file, e)

        # Add package metadata to each rule
        for rule in rules:
            rule["_package"] = package_name
            rule["_package_version"] = package["version"]

        return rules

    def build_catalog(self) -> dict[str, list[dict[str, Any]]]:
        """
        Build complete catalog of all rules.

        Returns:
            Catalog organized by package
        """
        catalog = {}

        for package_name in self.packages:
            try:
                rules = self.extract_rules(package_name)
                catalog[package_name] = rules

                # Index by ruleID
                for rule in rules:
                    rule_id = rule.get("ruleID")
                    if rule_id:
                        self.rules[rule_id] = rule

            except (OSError, ValueError, KeyError) as e:
                logger.error("Failed to catalog package %s: %s", package_name, e)

        return catalog

    def get_rule(self, rule_id: str) -> dict[str, Any] | None:
        """
        Get rule by ID.

        Args:
            rule_id: Rule identifier

        Returns:
            Rule definition or None
        """
        return self.rules.get(rule_id)

    def search_rules(self, package: str | None = None, category: str | None = None, labels: list[str] | None = None) -> list[dict[str, Any]]:
        """
        Search rules by criteria.

        Args:
            package: Package name filter
            category: Category filter (mandatory, optional, potential)
            labels: Label filters

        Returns:
            Matching rules
        """
        results = []

        for rule in self.rules.values():
            # Package filter
            if package and rule.get("_package") != package:
                continue

            # Category filter
            if category and rule.get("category") != category:
                continue

            # Labels filter
            if labels:
                rule_labels = rule.get("labels", [])
                if not all(label in rule_labels for label in labels):
                    continue

            results.append(rule)

        return results
