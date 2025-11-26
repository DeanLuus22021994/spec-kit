#!/usr/bin/env python3
"""
Coverage Analyzer
Calculate validation rule coverage against best practices.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class CoverageAnalyzer:
    """Analyzes rule coverage against best practices."""

    def __init__(self, rules_root: Path, best_practices_file: Path):
        """
        Initialize analyzer.

        Args:
            rules_root: Root directory for validation rules
            best_practices_file: Path to best practices YAML
        """
        self.rules_root = rules_root
        self.best_practices_file = best_practices_file

    def load_best_practices(self) -> list[dict[str, Any]]:
        """Load best practices from file."""
        if not self.best_practices_file.exists():
            logger.warning("Best practices file not found: %s", self.best_practices_file)
            return []

        with open(self.best_practices_file, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return list(data.get("rules", []))

    def load_implemented_rules(self) -> list[dict[str, Any]]:
        """Load all implemented rules."""
        rules: list[dict[str, Any]] = []

        if not self.rules_root.exists():
            return rules

        for package_dir in self.rules_root.iterdir():
            if not package_dir.is_dir():
                continue

            rules_dir = package_dir / "rules"
            if not rules_dir.exists():
                continue

            for rule_file in rules_dir.glob("*.yaml"):
                try:
                    with open(rule_file, encoding="utf-8") as f:
                        rule = yaml.safe_load(f) or {}

                    rule["_package"] = package_dir.name
                    rule["_file"] = str(rule_file)
                    rules.append(rule)

                except (OSError, yaml.YAMLError) as e:
                    logger.warning("Failed to load rule %s: %s", rule_file, e)

        return rules

    def calculate_coverage(self) -> dict[str, Any]:
        """Calculate coverage metrics."""
        best_practices = self.load_best_practices()
        implemented_rules = self.load_implemented_rules()

        # Extract rule IDs
        bp_ids = {bp.get("id") for bp in best_practices if bp.get("id")}
        impl_ids = {rule.get("ruleID") for rule in implemented_rules if rule.get("ruleID")}

        # Calculate coverage
        covered = bp_ids.intersection(impl_ids)
        not_covered = bp_ids - impl_ids

        # Calculate category coverage
        category_coverage = self._calculate_category_coverage(best_practices, implemented_rules)

        # Calculate effort coverage
        effort_stats = self._calculate_effort_stats(implemented_rules)

        total_bp = len(bp_ids)
        covered_count = len(covered)
        coverage_percent = (covered_count / total_bp * 100) if total_bp > 0 else 0

        return {
            "total_best_practices": total_bp,
            "covered": covered_count,
            "not_covered": len(not_covered),
            "coverage_percent": coverage_percent,
            "covered_ids": sorted([x for x in covered if x is not None]),
            "not_covered_ids": sorted([x for x in not_covered if x is not None]),
            "total_implemented_rules": len(implemented_rules),
            "category_coverage": category_coverage,
            "effort_stats": effort_stats,
        }

    def _calculate_category_coverage(  # pylint: disable=unused-argument
        self, best_practices: list[dict[str, Any]], implemented_rules: list[dict[str, Any]]
    ) -> dict[str, int]:
        """Calculate coverage by category."""
        category_stats: dict[str, int] = {}

        for rule in implemented_rules:
            category = rule.get("category", "uncategorized")
            if category not in category_stats:
                category_stats[category] = 0
            category_stats[category] += 1

        return category_stats

    def _calculate_effort_stats(self, rules: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate effort statistics."""
        effort_counts: dict[int, int] = {}
        total_effort = 0

        for rule in rules:
            effort = rule.get("effort", 0)
            effort_counts[effort] = effort_counts.get(effort, 0) + 1
            total_effort += effort

        avg_effort = total_effort / len(rules) if rules else 0

        return {
            "total_effort": total_effort,
            "average_effort": avg_effort,
            "effort_distribution": effort_counts,
        }

    def generate_report(self, output_format: str = "text") -> str:
        """Generate coverage report."""
        coverage = self.calculate_coverage()

        if output_format == "json":
            return json.dumps(coverage, indent=2)
        if output_format == "yaml":
            return yaml.dump(coverage, default_flow_style=False, sort_keys=False)
        return self._format_text_report(coverage)

    def _format_text_report(self, coverage: dict[str, Any]) -> str:
        """Format coverage report as text."""
        lines = []
        lines.append("=" * 60)
        lines.append("RULE COVERAGE REPORT")
        lines.append("=" * 60)

        lines.append("\nOverall Coverage:")
        lines.append(f"  Best Practices: {coverage['total_best_practices']}")
        lines.append(f"  Covered: {coverage['covered']} ({coverage['coverage_percent']:.1f}%)")
        lines.append(f"  Not Covered: {coverage['not_covered']}")
        lines.append(f"  Total Implemented: {coverage['total_implemented_rules']}")

        lines.append("\nCategory Breakdown:")
        for category, count in sorted(coverage["category_coverage"].items()):
            lines.append(f"  {category}: {count}")

        lines.append("\nEffort Statistics:")
        effort_stats = coverage["effort_stats"]
        lines.append(f"  Total Effort: {effort_stats['total_effort']}")
        lines.append(f"  Average Effort: {effort_stats['average_effort']:.1f}")
        lines.append("  Distribution:")
        for effort, count in sorted(effort_stats["effort_distribution"].items()):
            lines.append(f"    Effort {effort}: {count} rules")

        if coverage["not_covered_ids"]:
            lines.append(f"\nNot Covered ({len(coverage['not_covered_ids'])}):")
            for rule_id in coverage["not_covered_ids"][:10]:  # Show first 10
                lines.append(f"  - {rule_id}")
            if len(coverage["not_covered_ids"]) > 10:
                lines.append(f"  ... and {len(coverage['not_covered_ids']) - 10} more")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Coverage analyzer")
    parser.add_argument("--best-practices", type=Path, help="Path to best practices YAML file")
    parser.add_argument("--format", choices=["text", "json", "yaml"], default="text", help="Output format")
    parser.add_argument("--output", "-o", type=Path, help="Output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")

    # Determine paths
    project_root = Path(__file__).parent.parent.parent.parent
    rules_root = project_root / "tools" / ".config" / "validation" / "packages"

    if args.best_practices:
        bp_file = args.best_practices
    else:
        bp_file = project_root / "tools" / ".config" / "validation" / "yaml-best-practices.yml"

    # Analyze coverage
    analyzer = CoverageAnalyzer(rules_root, bp_file)
    report = analyzer.generate_report(args.format)

    # Output report
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        logger.info("Report saved to: %s", args.output)
    else:
        print(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
