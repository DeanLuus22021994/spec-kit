#!/usr/bin/env python3
"""
Rule Scaffolder
Generate validation rule templates with interactive prompts.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class RuleScaffolder:
    """Interactive rule scaffolder."""

    def __init__(self, rules_root: Path):
        """
        Initialize scaffolder.

        Args:
            rules_root: Root directory for validation rules
        """
        self.rules_root = rules_root

    def prompt_for_details(self) -> dict[str, Any]:
        """
        Interactively prompt for rule details.

        Returns:
            Dictionary of rule details
        """
        print("\n" + "=" * 60)
        print("RULE SCAFFOLDER")
        print("=" * 60)

        rule_name, rule_id = self._prompt_rule_name()
        package = self._prompt_package()
        category = self._prompt_category()
        effort = self._prompt_effort()
        description, tags, message = self._prompt_metadata()

        return {
            "rule_id": rule_id,
            "rule_name": rule_name,
            "package": package,
            "category": category,
            "effort": effort,
            "description": description,
            "tags": tags,
            "message": message or "Validation failed",
        }

    def _prompt_rule_name(self) -> tuple[str, str]:
        """Prompt for rule name and generate ID."""
        rule_name = input("\nRule name (human-readable): ").strip()
        rule_id = rule_name.lower().replace(" ", "-").replace("_", "-")
        print(f"Rule ID: {rule_id}")
        return rule_name, rule_id

    def _prompt_package(self) -> str:
        """Prompt for package selection."""
        print("\nSelect package:")
        packages = self._list_packages()
        for i, pkg in enumerate(packages, 1):
            print(f"  {i}. {pkg}")
        print(f"  {len(packages) + 1}. Create new package")

        pkg_choice = input(f"Choice (1-{len(packages) + 1}): ").strip()
        if pkg_choice.isdigit() and int(pkg_choice) == len(packages) + 1:
            return input("New package name: ").strip()
        if pkg_choice.isdigit() and 1 <= int(pkg_choice) <= len(packages):
            return packages[int(pkg_choice) - 1]
        return "custom"

    def _prompt_category(self) -> str:
        """Prompt for category selection."""
        print("\nSelect category:")
        categories = ["structure", "style", "security", "performance", "maintainability"]
        for i, cat in enumerate(categories, 1):
            print(f"  {i}. {cat}")

        cat_choice = input(f"Choice (1-{len(categories)}): ").strip()
        if cat_choice.isdigit() and 1 <= int(cat_choice) <= len(categories):
            return categories[int(cat_choice) - 1]
        return "style"

    def _prompt_effort(self) -> int:
        """Prompt for effort level."""
        print("\nEffort (Fibonacci scale):")
        efforts = {"0": "Trivial", "1": "Easy", "3": "Medium", "5": "Hard", "7": "Very Hard", "13": "Extreme"}
        for effort_str, desc in efforts.items():
            print(f"  {effort_str}: {desc}")

        effort_input = input("Effort level (0/1/3/5/7/13): ").strip()
        return int(effort_input) if effort_input in efforts else 3

    def _prompt_metadata(self) -> tuple[str, list[str], str]:
        """Prompt for description, tags, and message."""
        description = input("\nBrief description: ").strip()
        tags_input = input("Tags (comma-separated): ").strip()
        tags = [t.strip() for t in tags_input.split(",")] if tags_input else ["yaml"]
        message = input("\nError message template: ").strip()
        return description, tags, message

    def _list_packages(self) -> list[str]:
        """List existing packages."""
        if not self.rules_root.exists():
            return []

        return [d.name for d in self.rules_root.iterdir() if d.is_dir() and not d.name.startswith(".")]

    def generate_rule(self, details: dict[str, Any]) -> str:
        """
        Generate rule YAML content.

        Args:
            details: Rule details

        Returns:
            YAML content
        """
        rule = {
            "ruleID": details["rule_id"],
            "name": details["rule_name"],
            "description": details["description"],
            "category": details["category"],
            "effort": details["effort"],
            "tags": details["tags"],
            "when": [
                {
                    "filePattern": "*.yaml",
                }
            ],
            "perform": [{"action": "validate", "message": "TODO: Define validation logic"}],
            "message": details["message"],
            "examples": [
                {"title": "Valid example", "code": "# TODO: Provide valid example\n"},
                {"title": "Invalid example", "code": "# TODO: Provide invalid example\n"},
            ],
        }

        return yaml.dump(rule, default_flow_style=False, sort_keys=False)

    def generate_test(self, details: dict[str, Any]) -> str:
        """Generate test YAML content."""
        test = {
            "name": f"{details['rule_name']} Tests",
            "ruleID": details["rule_id"],
            "description": f"Test cases for {details['rule_id']}",
            "cases": [
                {
                    "name": "Should pass with valid YAML",
                    "fixture": f"fixtures/{details['rule_id']}-valid.yaml",
                    "expectMatch": False,
                    "description": "Valid YAML should not trigger the rule",
                },
                {
                    "name": "Should fail with invalid YAML",
                    "fixture": f"fixtures/{details['rule_id']}-invalid.yaml",
                    "expectMatch": True,
                    "description": "Invalid YAML should trigger the rule",
                },
            ],
        }

        return yaml.dump(test, default_flow_style=False, sort_keys=False)

    def create_rule_files(self, details: dict[str, Any]) -> None:
        """
        Create all rule files.

        Args:
            details: Rule details
        """
        package_dir = self.rules_root / details["package"]
        rules_dir = package_dir / "rules"
        tests_dir = package_dir / "tests"
        fixtures_dir = package_dir / "fixtures"

        # Create directories
        rules_dir.mkdir(parents=True, exist_ok=True)
        tests_dir.mkdir(parents=True, exist_ok=True)
        fixtures_dir.mkdir(parents=True, exist_ok=True)

        # Create rule file
        rule_path = rules_dir / f"{details['rule_id']}.yaml"
        rule_content = self.generate_rule(details)
        rule_path.write_text(rule_content, encoding="utf-8")
        print(f"✓ Created: {rule_path}")

        # Create test file
        test_path = tests_dir / f"{details['rule_id']}.test.yaml"
        test_content = self.generate_test(details)
        test_path.write_text(test_content, encoding="utf-8")
        print(f"✓ Created: {test_path}")

        # Create fixtures
        valid_fixture = fixtures_dir / f"{details['rule_id']}-valid.yaml"
        invalid_fixture = fixtures_dir / f"{details['rule_id']}-invalid.yaml"

        valid_fixture.write_text("# Valid fixture\nkey: value\n", encoding="utf-8")
        invalid_fixture.write_text("# Invalid fixture\nkey: value\n", encoding="utf-8")
        print(f"✓ Created: {valid_fixture}")
        print(f"✓ Created: {invalid_fixture}")

        # Update ruleset
        self._update_ruleset(package_dir, details["rule_id"])

        print("\n" + "=" * 60)
        print("SCAFFOLDING COMPLETE")
        print("=" * 60)
        print("\nNext steps:")
        print(f"  1. Edit {rule_path}")
        print(f"  2. Customize test cases in {test_path}")
        print(f"  3. Update fixtures: {fixtures_dir}")
        print(f"  4. Run tests: validate test --package {details['package']}")
        print()

    def _update_ruleset(self, package_dir: Path, rule_id: str) -> None:
        """Update package ruleset."""
        ruleset_path = package_dir / "ruleset.yaml"

        if ruleset_path.exists():
            with open(ruleset_path, encoding="utf-8") as f:
                ruleset = yaml.safe_load(f) or {}
        else:
            ruleset = {"name": package_dir.name, "rules": []}

        rule_ref = f"rules/{rule_id}.yaml"
        if rule_ref not in ruleset.get("rules", []):
            ruleset.setdefault("rules", []).append(rule_ref)
            ruleset["rules"] = sorted(ruleset["rules"])

        with open(ruleset_path, "w", encoding="utf-8") as f:
            yaml.dump(ruleset, f, default_flow_style=False, sort_keys=False)

        print(f"✓ Updated: {ruleset_path}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Rule scaffolder")
    parser.add_argument("--non-interactive", action="store_true", help="Non-interactive mode")
    parser.add_argument("--rule-id", help="Rule ID")
    parser.add_argument("--package", default="custom", help="Package name")
    parser.add_argument("--category", default="style", help="Rule category")

    args = parser.parse_args()

    # Determine project root
    project_root = Path(__file__).parent.parent.parent.parent
    rules_root = project_root / "tools" / ".config" / "validation" / "packages"

    scaffolder = RuleScaffolder(rules_root)

    if args.non_interactive:
        # Non-interactive mode
        if not args.rule_id:
            print("Error: --rule-id required in non-interactive mode")
            return 1

        details = {
            "rule_id": args.rule_id,
            "rule_name": args.rule_id.replace("-", " ").title(),
            "package": args.package,
            "category": args.category,
            "effort": 3,
            "description": f"Validation rule: {args.rule_id}",
            "tags": ["yaml"],
            "message": "Validation failed",
        }
    else:
        # Interactive mode
        details = scaffolder.prompt_for_details()

    scaffolder.create_rule_files(details)
    return 0


if __name__ == "__main__":
    sys.exit(main())
