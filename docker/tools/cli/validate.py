#!/usr/bin/env python3
# pylint: disable=wrong-import-position,redefined-builtin,redefined-outer-name
"""YAML Validation CLI.

Main entry point for validation commands.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

# Add parent directory to path for imports
# Note: Imports below intentionally come after sys.path modification
sys.path.insert(0, str(Path(__file__).parent.parent))

# Imports below are intentionally after sys.path modification
from .commands.profile import manage_profiles  # noqa: E402
from .commands.report import generate_report  # noqa: E402
from .commands.run import run_validation  # noqa: E402
from .commands.scaffold import scaffold_rule  # noqa: E402
from .commands.test import test_rules  # noqa: E402

logger = logging.getLogger(__name__)


def _cli_impl(ctx: click.Context, verbose: bool, quiet: bool) -> None:
    """
    YAML Validation CLI implementation.

    A comprehensive tool for validating YAML files, managing validation rules,
    and generating reports.

    Examples:
        # Run validation with default profile
        validate run

        # Run validation with specific profile
        validate run --profile strict

        # Test all validation rules
        validate test

        # Generate a new rule
        validate scaffold my-new-rule

        # Generate validation report
        validate report --format html
    """
    ctx.ensure_object(dict)

    # Configure logging
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    elif quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.INFO)

    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
@click.version_option(version="1.0.0")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, quiet: bool) -> None:
    """YAML Validation CLI."""
    _cli_impl(ctx, verbose, quiet)


@cli.command()
@click.option("--profile", "-p", default="recommended", help="Validation profile to use (recommended, strict, minimal)")
@click.option("--input", "-i", type=click.Path(exists=True), default=".", help="Input directory or file to validate")
@click.option("--output", "-o", type=click.Path(), help="Output file for validation results")
@click.option("--format", "-f", type=click.Choice(["text", "json", "yaml", "html", "markdown"]), default="text", help="Output format")
@click.option("--fail-on-error", is_flag=True, help="Exit with non-zero code on validation errors")
@click.option("--fail-on-warning", is_flag=True, help="Exit with non-zero code on validation warnings")
@click.option("--watch", "-w", is_flag=True, help="Watch for file changes and re-validate")
@click.pass_context
def run(
    ctx: click.Context,
    profile: str,
    input: str,
    output: str | None,
    format: str,
    fail_on_error: bool,
    fail_on_warning: bool,
    watch: bool,
) -> None:
    """
    Run YAML validation.

    Validates YAML files against configured rules and profiles.

    Examples:
        # Validate current directory with recommended profile
        validate run

        # Validate specific directory with strict profile
        validate run --profile strict --input .config/

        # Generate JSON report
        validate run --format json --output report.json

        # Watch mode for continuous validation
        validate run --watch
    """
    exit_code = run_validation(
        profile=profile,
        input_path=Path(input),
        output_path=Path(output) if output else None,
        output_format=format,
        fail_on_error=fail_on_error,
        fail_on_warning=fail_on_warning,
        watch=watch,
        verbose=ctx.obj["verbose"],
    )

    sys.exit(exit_code)


@cli.command()
@click.option("--package", "-p", help="Test specific package only")
@click.option("--rule", "-r", help="Test specific rule only")
@click.option("--coverage", is_flag=True, help="Generate coverage report")
@click.option("--output", "-o", type=click.Path(), help="Output file for test results")
@click.pass_context
def test(
    ctx: click.Context,
    package: str | None,
    rule: str | None,
    coverage: bool,
    output: str | None,
) -> None:
    """
    Test validation rules.

    Runs test suites for validation rules to ensure they work correctly.

    Examples:
        # Test all rules
        validate test

        # Test specific package
        validate test --package metadata

        # Test with coverage report
        validate test --coverage
    """
    exit_code = test_rules(package=package, rule=rule, coverage=coverage, output_path=Path(output) if output else None, verbose=ctx.obj["verbose"])

    sys.exit(exit_code)


@cli.command()
@click.argument("rule-name")
@click.option("--package", "-p", help="Package to create rule in (default: custom)")
@click.option("--category", "-c", type=click.Choice(["structure", "style", "security", "performance", "maintainability"]), help="Rule category")
@click.option("--effort", "-e", type=click.Choice(["0", "1", "3", "5", "7", "13"]), help="Remediation effort (Fibonacci scale)")
@click.option("--interactive", "-i", is_flag=True, default=True, help="Interactive mode with prompts")
@click.pass_context
def scaffold(
    ctx: click.Context,
    rule_name: str,
    package: str | None,
    category: str | None,
    effort: str | None,
    interactive: bool,
) -> None:
    """
    Generate new validation rule.

    Creates a new validation rule from template with all necessary files:
    - Rule YAML definition
    - Test file
    - Test fixtures

    Examples:
        # Interactive mode (default)
        validate scaffold my-rule

        # Non-interactive with options
        validate scaffold my-rule --package custom --category style --effort 3
    """
    exit_code = scaffold_rule(
        rule_name=rule_name,
        package=package,
        category=category,
        effort=int(effort) if effort else None,
        interactive=interactive,
        verbose=ctx.obj["verbose"],
    )

    sys.exit(exit_code)


@cli.command()
@click.argument("action", type=click.Choice(["list", "show", "create", "edit"]))
@click.argument("profile-name", required=False)
@click.option("--output", "-o", type=click.Path(), help="Output file for profile")
@click.pass_context
def profile(
    ctx: click.Context,
    action: str,
    profile_name: str | None,
    output: str | None,
) -> None:
    """
    Manage validation profiles.

    Profiles define sets of rules to apply during validation.

    Examples:
        # List all profiles
        validate profile list

        # Show profile details
        validate profile show strict

        # Create new profile
        validate profile create my-profile
    """
    exit_code = manage_profiles(action=action, profile_name=profile_name, output_path=Path(output) if output else None, verbose=ctx.obj["verbose"])

    sys.exit(exit_code)


@cli.command()
@click.option("--format", "-f", type=click.Choice(["text", "json", "yaml", "html", "markdown"]), default="html", help="Report format")
@click.option("--output", "-o", type=click.Path(), help="Output file for report")
@click.option("--include-coverage", is_flag=True, help="Include rule coverage analysis")
@click.option("--include-trends", is_flag=True, help="Include historical trends")
@click.pass_context
def report(
    ctx: click.Context,
    format: str,
    output: str | None,
    include_coverage: bool,
    include_trends: bool,
) -> None:
    """
    Generate validation reports.

    Creates comprehensive reports on validation results, coverage, and trends.

    Examples:
        # Generate HTML report
        validate report --format html --output report.html

        # Generate report with coverage
        validate report --include-coverage
    """
    exit_code = generate_report(
        output_format=format,
        output_path=Path(output) if output else None,
        include_coverage=include_coverage,
        include_trends=include_trends,
        verbose=ctx.obj["verbose"],
    )

    sys.exit(exit_code)


def main() -> None:
    """Main entry point for the CLI."""
    # Click's decorator transforms the function signature
    # Call with no arguments - Click handles arg parsing from sys.argv
    sys.exit(cli.main(standalone_mode=False) or 0)


if __name__ == "__main__":
    main()
