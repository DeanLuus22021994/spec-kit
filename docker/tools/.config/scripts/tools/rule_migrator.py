#!/usr/bin/env python3
"""
Rule Migrator
Migrate old validation rules to new structure.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class RuleMigrator:
    """Migrates rules from old format to new format."""

    def __init__(self, source_dir: Path, target_dir: Path):
        """
        Initialize migrator.

        Args:
            source_dir: Source directory with old rules
            target_dir: Target directory for new rules
        """
        self.source_dir = source_dir
        self.target_dir = target_dir

    def migrate_rule(self, old_rule_path: Path) -> Path:
        """
        Migrate a single rule.

        Args:
            old_rule_path: Path to old rule file

        Returns:
            Path to new rule file
        """
        # Load old rule
        with open(old_rule_path, encoding="utf-8") as f:
            old_rule = yaml.safe_load(f) or {}

        # Transform to new format
        new_rule = self._transform_rule(old_rule)

        # Determine new path
        rule_id = new_rule.get("ruleID", old_rule_path.stem)
        package = self._determine_package(new_rule)

        package_dir = self.target_dir / package / "rules"
        package_dir.mkdir(parents=True, exist_ok=True)

        new_rule_path = package_dir / f"{rule_id}.yaml"

        # Write new rule
        with open(new_rule_path, "w", encoding="utf-8") as f:
            yaml.dump(new_rule, f, default_flow_style=False, sort_keys=False)

        logger.info("Migrated: %s -> %s", old_rule_path.name, new_rule_path)
        return new_rule_path

    def _transform_rule(self, old_rule: dict[str, Any]) -> dict[str, Any]:
        """Transform old rule format to new format."""
        # Map old fields to new fields
        new_rule = {}

        # Direct mappings
        field_mappings = {
            "id": "ruleID",
            "ruleID": "ruleID",
            "name": "name",
            "description": "description",
            "category": "category",
            "effort": "effort",
            "tags": "tags",
            "message": "message",
        }

        for old_field, new_field in field_mappings.items():
            if old_field in old_rule:
                new_rule[new_field] = old_rule[old_field]

        # Transform 'when' conditions
        if "when" in old_rule:
            new_rule["when"] = old_rule["when"]
        else:
            # Default when condition
            new_rule["when"] = [{"filePattern": "*.yaml"}]

        # Transform 'perform' actions
        if "perform" in old_rule:
            new_rule["perform"] = old_rule["perform"]
        elif "actions" in old_rule:
            # Convert old 'actions' to 'perform'
            new_rule["perform"] = old_rule["actions"]
        else:
            new_rule["perform"] = [{"action": "validate"}]

        # Set defaults
        if "ruleID" not in new_rule:
            new_rule["ruleID"] = old_rule.get("id", "unknown")

        if "category" not in new_rule:
            new_rule["category"] = "style"

        if "effort" not in new_rule:
            new_rule["effort"] = 3

        return new_rule

    def _determine_package(self, rule: dict[str, Any]) -> str:
        """Determine appropriate package for rule."""
        category = rule.get("category", "style")
        tags = rule.get("tags", [])

        # Tag-based package assignment
        tag_to_package = {
            "metadata": "metadata",
            "indentation": "indentation",
            "formatting": "indentation",
            "quoting": "quoting",
            "anchor": "anchors",
            "reference": "anchors",
        }
        for tag, pkg in tag_to_package.items():
            if tag in tags:
                return pkg

        # Category-based fallback
        category_to_package = {"security": "security", "performance": "performance"}
        return category_to_package.get(category, "custom")

    def migrate_all_rules(self) -> None:
        """Migrate all rules in source directory."""
        if not self.source_dir.exists():
            logger.error("Source directory not found: %s", self.source_dir)
            return

        rule_files = list(self.source_dir.glob("**/*.yaml"))
        logger.info("Found %s rule files to migrate", len(rule_files))

        migrated = 0
        failed = 0

        for rule_file in rule_files:
            try:
                self.migrate_rule(rule_file)
                migrated += 1
            except (OSError, ValueError, yaml.YAMLError) as e:
                logger.error("Failed to migrate %s: %s", rule_file.name, e)
                failed += 1

        print("\nMigration complete:")
        print(f"  Migrated: {migrated}")
        print(f"  Failed: {failed}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Rule migrator")
    parser.add_argument("source", type=Path, help="Source directory with old rules")
    parser.add_argument("--target", type=Path, help="Target directory for new rules")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")

    # Determine target directory
    if args.target:
        target_dir = args.target
    else:
        project_root = Path(__file__).parent.parent.parent.parent
        target_dir = project_root / "tools" / ".config" / "validation" / "packages"

    migrator = RuleMigrator(args.source, target_dir)
    migrator.migrate_all_rules()

    return 0


if __name__ == "__main__":
    sys.exit(main())
