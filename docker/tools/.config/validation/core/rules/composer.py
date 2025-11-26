#!/usr/bin/env python3
"""
Ruleset Composer
Composes custom rulesets from profiles and filters.
"""
from __future__ import annotations

import logging
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .registry import RuleRegistry

_yaml: ModuleType | None
try:
    import yaml as _yaml_module

    _yaml = _yaml_module
except ImportError:
    _yaml = None

logger = logging.getLogger(__name__)


class RulesetComposer:
    """
    Dynamic ruleset composition based on profiles.

    Takes profile definitions and composes appropriate rulesets
    by selecting rules from packages based on criteria.
    """

    def __init__(self, profiles_dir: Path, rules_registry: RuleRegistry):
        """
        Initialize composer.

        Args:
            profiles_dir: Directory containing profile definitions
            rules_registry: RuleRegistry instance
        """
        if not _yaml:
            raise ImportError("PyYAML required for composer")

        self.profiles_dir = profiles_dir
        self.registry = rules_registry
        self.profiles: dict[str, dict[str, Any]] = {}

    def load_profile(self, profile_name: str) -> dict[str, Any]:
        """
        Load profile definition.

        Args:
            profile_name: Profile name (e.g., "strict", "recommended")

        Returns:
            Profile definition
        """
        profile_path = self.profiles_dir / f"{profile_name}.yaml"

        if not profile_path.exists():
            raise FileNotFoundError(f"Profile not found: {profile_path}")

        with open(profile_path, "r", encoding="utf-8") as f:
            profile: dict[str, Any] = _yaml.safe_load(f) if _yaml else {}

        self.profiles[profile_name] = profile
        logger.info("Loaded profile: %s", profile_name)

        return profile

    def compose_ruleset(self, profile_name: str, output_path: Path | None = None) -> dict[str, Any]:
        """
        Compose ruleset from profile.

        Args:
            profile_name: Profile name
            output_path: Optional path to write composed ruleset

        Returns:
            Composed ruleset
        """
        # Load profile if not cached
        if profile_name not in self.profiles:
            profile = self.load_profile(profile_name)
        else:
            profile = self.profiles[profile_name]

        # Extract rule selection criteria
        rule_config = profile.get("rules", {})

        # Compose ruleset
        ruleset = {
            "metadata": {
                "name": f"{profile_name}-ruleset",
                "version": "1.0.0",
                "profile": profile_name,
                "generated": True,
            },
            "rules": [],  # type: ignore[var-annotated]
        }

        # Select rules from each package
        for package_name, package_config in rule_config.items():
            selected_rules = self._select_package_rules(package_name, package_config)
            # Cast to list to avoid type checker issue
            rules_list: list = ruleset["rules"]  # type: ignore[assignment]
            rules_list.extend(selected_rules)

        logger.info("Composed ruleset '%s': %s rules", profile_name, len(ruleset["rules"]))

        # Write to file if requested
        if output_path:
            self._write_ruleset(ruleset, output_path)

        return ruleset

    def _select_package_rules(self, package_name: str, config: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Select rules from package based on config.

        Args:
            package_name: Package name
            config: Selection config

        Returns:
            Selected rules
        """
        # Get all rules from package
        try:
            all_rules = self.registry.extract_rules(package_name)
        except (OSError, ValueError, KeyError) as e:
            logger.error("Failed to extract rules from %s: %s", package_name, e)
            return []

        # Apply filters
        severity_filter = config.get("severity")
        all_enabled = config.get("all", False)

        selected = []

        for rule in all_rules:
            # If all=true, include all rules
            if all_enabled:
                selected.append(rule)
                continue

            # Filter by severity/category
            if severity_filter:
                rule_category = rule.get("category")

                # Handle list or single value
                if isinstance(severity_filter, list):
                    if rule_category in severity_filter:
                        selected.append(rule)
                elif rule_category == severity_filter:
                    selected.append(rule)

        logger.debug("Selected %s/%s rules from %s", len(selected), len(all_rules), package_name)

        return selected

    def _write_ruleset(self, ruleset: dict[str, Any], output_path: Path) -> None:
        """
        Write composed ruleset to file.

        Args:
            ruleset: Ruleset data
            output_path: Output file path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            if _yaml:
                _yaml.dump(ruleset, f, default_flow_style=False, sort_keys=False)

        logger.info("Wrote ruleset to: %s", output_path)

    def generate_label_selector(self, profile_name: str) -> str:
        """
        Generate Kantra label selector from profile.

        Args:
            profile_name: Profile name

        Returns:
            Label selector expression
        """
        if profile_name not in self.profiles:
            profile = self.load_profile(profile_name)
        else:
            profile = self.profiles[profile_name]

        rule_config = profile.get("rules", {})

        # Build label expressions for each package
        expressions = []

        for _package_name, config in rule_config.items():
            severity = config.get("severity")

            if isinstance(severity, list):
                # Multiple severities: (category=mandatory || category=optional)
                severity_expr = " || ".join([f"category={s}" for s in severity])
                expressions.append(f"({severity_expr})")
            elif severity:
                expressions.append(f"category={severity}")

        # Combine with AND (all packages)
        if expressions:
            selector = " && ".join(expressions)
        else:
            selector = "category=mandatory"  # Default

        logger.debug("Label selector for %s: %s", profile_name, selector)

        return selector

    def list_profiles(self) -> list[str]:
        """
        List available profiles.

        Returns:
            List of profile names
        """
        if not self.profiles_dir.exists():
            return []

        profiles = [p.stem for p in self.profiles_dir.glob("*.yaml")]

        return sorted(profiles)
