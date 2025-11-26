#!/usr/bin/env python3
"""Scaffold Command.

Generate new validation rules from templates.
"""

from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


@dataclass
class ScaffoldConfig:
    """Configuration for rule scaffolding."""

    rule_id: str
    rule_name: str
    package: str
    category: str
    effort: int
    package_dir: Path


def scaffold_rule(
    rule_name: str,
    package: str | None,
    category: str | None,
    effort: int | None,
    interactive: bool,
    verbose: bool,
) -> int:
    """Generate new validation rule.

    Args:
        rule_name: Name of the rule.
        package: Package name.
        category: Rule category.
        effort: Remediation effort.
        interactive: Use interactive prompts.
        verbose: Verbose output.

    Returns:
        Exit code.
    """
    try:
        config = _build_config(rule_name, package, category, effort, interactive)
        return _execute_scaffold(config)

    except (OSError, ValueError, yaml.YAMLError) as e:
        logger.error("Scaffolding failed: %s", e)
        if verbose:
            traceback.print_exc()
        return 1


def _build_config(
    rule_name: str,
    package: str | None,
    category: str | None,
    effort: int | None,
    interactive: bool,
) -> ScaffoldConfig:
    """Build scaffold configuration from inputs.

    Args:
        rule_name: Name of the rule.
        package: Package name.
        category: Rule category.
        effort: Remediation effort.
        interactive: Use interactive prompts.

    Returns:
        Configured ScaffoldConfig instance.
    """
    rule_id = rule_name.lower().replace(" ", "-")
    logger.info("Scaffolding rule: %s", rule_id)

    if interactive:
        package, category, effort = _prompt_interactive(package, category, effort)

    project_root = Path(__file__).parent.parent.parent.parent
    package_name = package or "custom"
    package_dir = project_root / "tools" / ".config" / "validation" / "packages" / package_name

    return ScaffoldConfig(
        rule_id=rule_id,
        rule_name=rule_name,
        package=package_name,
        category=category or "style",
        effort=effort if effort is not None else 3,
        package_dir=package_dir,
    )


def _prompt_interactive(
    package: str | None,
    category: str | None,
    effort: int | None,
) -> tuple[str, str, int]:
    """Handle interactive prompts for missing values.

    Args:
        package: Optional package name.
        category: Optional category.
        effort: Optional effort level.

    Returns:
        Tuple of (package, category, effort) values.
    """
    if not package:
        package = input("Package name (default: custom): ").strip() or "custom"

    if not category:
        categories = ["structure", "style", "security", "performance", "maintainability"]
        print("\nCategories:")
        for i, cat in enumerate(categories, 1):
            print(f"  {i}. {cat}")
        choice = input("Select category (1-5): ").strip()
        category = categories[int(choice) - 1] if choice.isdigit() and 1 <= int(choice) <= 5 else "style"

    if effort is None:
        print("\nEffort levels (Fibonacci scale):")
        print("  0 - No effort required")
        print("  1 - Trivial (seconds)")
        print("  3 - Easy (minutes)")
        print("  5 - Medium (1-2 hours)")
        print("  7 - Hard (half day)")
        print("  13 - Very hard (full day+)")
        effort_input = input("Select effort (0/1/3/5/7/13): ").strip()
        effort = int(effort_input) if effort_input.isdigit() else 3

    return package, category, effort  # type: ignore[return-value]


def _execute_scaffold(config: ScaffoldConfig) -> int:
    """Execute the scaffolding with prepared configuration.

    Args:
        config: Scaffold configuration.

    Returns:
        Exit code.
    """
    # Create directory structure
    rules_dir = config.package_dir / "rules"
    tests_dir = config.package_dir / "tests"
    fixtures_dir = config.package_dir / "fixtures"

    for directory in [rules_dir, tests_dir, fixtures_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    # Check for existing rule
    rule_path = rules_dir / f"{config.rule_id}.yaml"
    if rule_path.exists():
        logger.warning("Rule already exists: %s", rule_path)
        if input("Overwrite? (y/N): ").strip().lower() != "y":
            logger.info("Cancelled")
            return 0

    # Generate files
    _write_rule_files(config, rules_dir, tests_dir, fixtures_dir)
    update_package_ruleset(config.package_dir, config.rule_id)

    # Print summary
    _print_summary(config, rule_path, tests_dir, fixtures_dir)
    return 0


def _write_rule_files(
    config: ScaffoldConfig,
    rules_dir: Path,
    tests_dir: Path,
    fixtures_dir: Path,
) -> None:
    """Write all scaffolded files.

    Args:
        config: Scaffold configuration.
        rules_dir: Directory for rule files.
        tests_dir: Directory for test files.
        fixtures_dir: Directory for fixture files.
    """
    rule_path = rules_dir / f"{config.rule_id}.yaml"
    rule_path.write_text(generate_rule_template(config.rule_id, config.rule_name, config.category, config.effort), encoding="utf-8")
    logger.info("Created rule: %s", rule_path)

    test_path = tests_dir / f"{config.rule_id}.test.yaml"
    test_path.write_text(generate_test_template(config.rule_id, config.rule_name), encoding="utf-8")
    logger.info("Created test: %s", test_path)

    valid_fixture = fixtures_dir / f"{config.rule_id}-valid.yaml"
    invalid_fixture = fixtures_dir / f"{config.rule_id}-invalid.yaml"
    valid_fixture.write_text(generate_valid_fixture(), encoding="utf-8")
    invalid_fixture.write_text(generate_invalid_fixture(), encoding="utf-8")
    logger.info("Created fixtures: %s", fixtures_dir)


def _print_summary(
    config: ScaffoldConfig,
    rule_path: Path,
    tests_dir: Path,
    fixtures_dir: Path,
) -> None:
    """Print scaffolding summary.

    Args:
        config: Scaffold configuration.
        rule_path: Path to the created rule file.
        tests_dir: Directory containing test files.
        fixtures_dir: Directory containing fixture files.
    """
    print("\n" + "=" * 60)
    print("RULE SCAFFOLDING COMPLETE")
    print("=" * 60)
    print(f"\nRule ID:    {config.rule_id}")
    print(f"Package:    {config.package}")
    print(f"Category:   {config.category}")
    print(f"Effort:     {config.effort}")
    print("\nFiles created:")
    print(f"  - {rule_path}")
    print(f"  - {tests_dir / f'{config.rule_id}.test.yaml'}")
    print(f"  - {fixtures_dir / f'{config.rule_id}-valid.yaml'}")
    print(f"  - {fixtures_dir / f'{config.rule_id}-invalid.yaml'}")
    print("\nNext steps:")
    print("  1. Edit the rule file to define validation logic")
    print("  2. Update test cases in the test file")
    print("  3. Customize fixtures for your use case")
    print(f"  4. Run tests: validate test --package {config.package}")
    print("\n" + "=" * 60 + "\n")


def generate_rule_template(
    rule_id: str,
    rule_name: str,
    category: str,
    effort: int,
) -> str:
    """Generate rule YAML template.

    Args:
        rule_id: Unique rule identifier.
        rule_name: Human-readable rule name.
        category: Rule category.
        effort: Remediation effort level.

    Returns:
        YAML template string.
    """
    template = f"""---
ruleID: {rule_id}
name: {rule_name}
description: >
  TODO: Describe what this rule validates

category: {category}
effort: {effort}
tags:
  - yaml
  - best-practices

when:
  # Define when this rule should be applied
  # Example:
  # - filePattern: "*.yaml"
  #   yamlPath: "metadata"
  - filePattern: "*.yaml"

perform:
  # Define validation logic
  # Example:
  # - action: checkExists
  #   target: "metadata.name"
  #   message: "metadata.name is required"
  - action: validate
    message: "TODO: Define validation action"

message: |
  TODO: Provide a clear error message explaining what went wrong
  and how to fix it.

examples:
  - title: Valid example
    code: |
      # TODO: Provide a valid example

  - title: Invalid example
    code: |
      # TODO: Provide an invalid example
"""
    return template


def generate_test_template(rule_id: str, rule_name: str) -> str:
    """Generate test YAML template.

    Args:
        rule_id: Unique rule identifier.
        rule_name: Human-readable rule name.

    Returns:
        YAML test template string.
    """
    template = f"""---
name: {rule_name} Tests
ruleID: {rule_id}
description: Test cases for {rule_id}

cases:
  - name: Should pass with valid YAML
    fixture: fixtures/{rule_id}-valid.yaml
    expectMatch: false
    description: Valid YAML should not trigger the rule

  - name: Should fail with invalid YAML
    fixture: fixtures/{rule_id}-invalid.yaml
    expectMatch: true
    description: Invalid YAML should trigger the rule

  - name: Edge case - TODO
    fixture: |
      # TODO: Add inline fixture for edge case
      key: value
    expectMatch: false
    description: TODO - describe edge case
"""
    return template


def generate_valid_fixture() -> str:
    """Generate valid fixture template.

    Returns:
        Valid fixture YAML string.
    """
    return """---
# Valid YAML fixture
# TODO: Customize this to match your rule's expectations

metadata:
  name: example
  version: "1.0.0"

data:
  key: value
"""


def generate_invalid_fixture() -> str:
    """Generate invalid fixture template.

    Returns:
        Invalid fixture YAML string.
    """
    return """---
# Invalid YAML fixture
# TODO: Customize this to violate your rule

data:
  key: value
# TODO: Add the problematic pattern here
"""


def update_package_ruleset(package_dir: Path, rule_id: str) -> None:
    """Update package ruleset.yaml to include new rule.

    Args:
        package_dir: Path to the package directory.
        rule_id: Rule identifier to add to ruleset.
    """
    ruleset_path = package_dir / "ruleset.yaml"

    if not ruleset_path.exists():
        # Create new ruleset
        ruleset = {"name": package_dir.name, "rules": [f"rules/{rule_id}.yaml"]}
    else:
        # Update existing ruleset
        with open(ruleset_path, "r", encoding="utf-8") as f:
            ruleset = yaml.safe_load(f) or {}

        rules = ruleset.get("rules", [])
        rule_ref = f"rules/{rule_id}.yaml"
        if isinstance(rules, list) and rule_ref not in rules:
            rules.append(rule_ref)
            ruleset["rules"] = sorted(rules)

    # Write updated ruleset
    with open(ruleset_path, "w", encoding="utf-8") as f:
        yaml.dump(ruleset, f, default_flow_style=False, sort_keys=False)

    logger.info("Updated ruleset: %s", ruleset_path)
