#!/usr/bin/env python3
"""
Test Generator
Automatically generate test files for validation rules.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class TestGenerator:
    """Generates test files for validation rules."""

    def __init__(self, rules_root: Path):
        """
        Initialize test generator.

        Args:
            rules_root: Root directory for validation rules
        """
        self.rules_root = rules_root

    def generate_tests_for_rule(self, rule_path: Path) -> dict[str, Any]:
        """
        Generate test file for a rule.

        Args:
            rule_path: Path to rule YAML file

        Returns:
            Test definition
        """
        # Load rule
        with open(rule_path, encoding="utf-8") as f:
            rule = yaml.safe_load(f) or {}

        rule_id = rule.get("ruleID")
        rule_name = rule.get("name", rule_id)

        # Generate test cases
        test_cases = []

        # Extract examples from rule if available
        examples = rule.get("examples", [])

        for i, example in enumerate(examples):
            title = example.get("title", f"Example {i+1}")
            code = example.get("code", "")

            # Determine if example is valid or invalid
            is_invalid = "invalid" in title.lower() or "wrong" in title.lower()

            test_cases.append({"name": f"Example: {title}", "fixture": code, "expectMatch": is_invalid, "description": title})

        # Add default test cases if no examples
        if not test_cases:
            test_cases = [
                {
                    "name": "Should pass with valid YAML",
                    "fixture": f"fixtures/{rule_id}-valid.yaml",
                    "expectMatch": False,
                    "description": "Valid YAML should not trigger the rule",
                },
                {
                    "name": "Should fail with invalid YAML",
                    "fixture": f"fixtures/{rule_id}-invalid.yaml",
                    "expectMatch": True,
                    "description": "Invalid YAML should trigger the rule",
                },
            ]

        # Create test definition
        test_def = {"name": f"{rule_name} Tests", "ruleID": rule_id, "description": f"Generated test cases for {rule_id}", "cases": test_cases}

        return test_def

    def generate_all_tests(self, package: str | None = None) -> None:
        """
        Generate tests for all rules.

        Args:
            package: Optional package name filter
        """
        if package:
            packages = [self.rules_root / package]
        else:
            packages = [d for d in self.rules_root.iterdir() if d.is_dir()]

        generated_count = 0

        for package_dir in packages:
            rules_dir = package_dir / "rules"
            tests_dir = package_dir / "tests"

            if not rules_dir.exists():
                continue

            tests_dir.mkdir(parents=True, exist_ok=True)

            for rule_file in rules_dir.glob("*.yaml"):
                test_path = tests_dir / f"{rule_file.stem}.test.yaml"

                # Skip if test already exists
                if test_path.exists():
                    logger.info("Test already exists: %s", test_path)
                    continue

                # Generate test
                test_def = self.generate_tests_for_rule(rule_file)

                # Write test file
                with open(test_path, "w", encoding="utf-8") as f:
                    yaml.dump(test_def, f, default_flow_style=False, sort_keys=False)

                logger.info("Generated test: %s", test_path)
                generated_count += 1

        print(f"\nGenerated {generated_count} test files")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test generator")
    parser.add_argument("--package", help="Package name to generate tests for")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")

    # Determine project root
    project_root = Path(__file__).parent.parent.parent.parent
    rules_root = project_root / "tools" / ".config" / "validation" / "packages"

    generator = TestGenerator(rules_root)
    generator.generate_all_tests(args.package)

    return 0


if __name__ == "__main__":
    sys.exit(main())
