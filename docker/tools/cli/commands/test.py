#!/usr/bin/env python3
"""Test Command.

Test validation rules with test harness.
"""

from __future__ import annotations

import json
import logging
import sys
import traceback
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from tools.config.validation.core.testing import TestHarness  # type: ignore[import]

    TEST_HARNESS_AVAILABLE = True
except ImportError:
    TEST_HARNESS_AVAILABLE = False
    TestHarness = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)


def test_rules(
    package: str | None,
    rule: str | None,
    coverage: bool,
    output_path: Path | None,
    verbose: bool,
) -> int:
    """Test validation rules.

    Args:
        package: Package name to test.
        rule: Specific rule to test.
        coverage: Generate coverage report.
        output_path: Output file path.
        verbose: Verbose output.

    Returns:
        Exit code.
    """
    try:
        if not TEST_HARNESS_AVAILABLE:
            logger.error("TestHarness not available. Check module path.")
            return 1

        # Determine project root
        project_root = Path(__file__).parent.parent.parent.parent
        rules_root = project_root / "tools" / ".config" / "validation" / "packages"
        test_data_root = project_root / "tools" / ".config" / "validation" / "test-data"

        # Initialize test harness
        harness = TestHarness(rules_root, test_data_root)

        # Run tests
        if rule:
            logger.info("Testing rule: %s", rule)
            # Find rule file
            rule_files = list(rules_root.glob(f"**/rules/{rule}.yaml"))
            if not rule_files:
                logger.error("Rule not found: %s", rule)
                return 1

            # Single rule testing not yet implemented
            logger.warning("Single rule testing not yet implemented")
            return 0

        package_info = f" for package: {package}" if package else ""
        logger.info("Running all tests%s", package_info)
        results = harness.run_all_tests(package)

        # Print results
        print_test_results(results, verbose)

        # Generate coverage if requested
        if coverage:
            generate_coverage_report(results, output_path)

        # Save results if output specified
        if output_path:
            save_test_results(results, output_path)

        # Return exit code based on results
        if results["failed"] > 0:
            return 1

        return 0

    except (OSError, ValueError, KeyError) as e:
        logger.error("Test execution failed: %s", e)
        if verbose:
            traceback.print_exc()
        return 1


def print_test_results(results: dict, verbose: bool) -> None:
    """Print test results to console.

    Args:
        results: Dictionary containing test results.
        verbose: Enable verbose output.
    """
    print("\n" + "=" * 60)
    print("VALIDATION RULE TEST RESULTS")
    print("=" * 60)

    total_tests = results.get("total_tests", 0)
    total_cases = results.get("total_cases", 0)
    passed = results.get("passed", 0)
    failed = results.get("failed", 0)

    print(f"\nTests:  {total_tests}")
    print(f"Cases:  {total_cases}")
    print(f"Passed: {passed} ✓")
    print(f"Failed: {failed} ✗")

    if total_cases > 0:
        pass_rate = (passed / total_cases) * 100
        print(f"\nPass Rate: {pass_rate:.1f}%")

    # Show details if verbose or failures exist
    if verbose or failed > 0:
        print("\n" + "-" * 60)
        print("DETAILED RESULTS")
        print("-" * 60)

        for test_result in results.get("results", []):
            if "error" in test_result:
                print(f"\n✗ {test_result['test_name']}")
                print(f"  Error: {test_result['error']}")
                continue

            test_name = test_result.get("test_name")
            rule_id = test_result.get("rule_id")
            test_passed = test_result.get("passed", 0)
            test_failed = test_result.get("failed", 0)

            status = "✓" if not test_failed else "✗"
            print(f"\n{status} {test_name} ({rule_id})")
            print(f"  Passed: {test_passed}, Failed: {test_failed}")

            if verbose or test_failed > 0:
                for case in test_result.get("results", []):
                    case_status = "✓" if case["passed"] else "✗"
                    print(f"    {case_status} {case['name']}")
                    if not case["passed"] and case.get("message"):
                        print(f"      {case['message']}")

    print("\n" + "=" * 60 + "\n")


def generate_coverage_report(results: dict, output_path: Path | None) -> None:
    """Generate test coverage report.

    Args:
        results: Dictionary containing test results.
        output_path: Optional path for the coverage report.
    """
    logger.info("Generating coverage report...")

    # Coverage analysis: calculate rule test coverage
    total_rules = results.get("total_tests", 0)
    covered_rules = results.get("passed", 0) + results.get("failed", 0)

    print("\nCoverage Report:")
    print(f"  Total Rules Tested: {total_rules}")
    print(f"  Rules with Results: {covered_rules}")
    if output_path:
        print(f"  Output Path: {output_path}")


def save_test_results(results: dict, output_path: Path) -> None:
    """Save test results to file.

    Args:
        results: Dictionary containing test results.
        output_path: Path to save the results file.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        logger.info("Results saved to: %s", output_path)

    except OSError as e:
        logger.error("Failed to save results: %s", e)
