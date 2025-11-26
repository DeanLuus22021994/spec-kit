#!/usr/bin/env python3
"""
Report Generator
Multi-format report generation and parsing for validation results.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
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


class ReportGenerator:
    """
    Validation report generation and parsing.

    Supports multiple output formats:
    - YAML (Kantra native)
    - JSON (CI/CD friendly)
    - HTML (human readable)
    - Markdown (documentation)
    """

    def __init__(self, reports_dir: Path):
        """
        Initialize report generator.

        Args:
            reports_dir: Base directory for reports
        """
        self.reports_dir = reports_dir
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def parse_kantra_output(self, output_path: Path) -> dict[str, Any]:
        """
        Parse Kantra output.yaml report.

        Args:
            output_path: Path to output.yaml

        Returns:
            Parsed report data
        """
        if not _yaml:
            raise ImportError("PyYAML required for report parsing")

        if not output_path.exists():
            logger.warning("Report not found: %s", output_path)
            return {}

        with open(output_path, "r", encoding="utf-8") as f:
            data = _yaml.safe_load(f)

        return data or {}

    def generate_summary(self, report_data: dict[str, Any]) -> dict[str, Any]:
        """
        Generate summary from report data.

        Args:
            report_data: Parsed report data

        Returns:
            Summary statistics
        """
        incidents = report_data.get("incidents", [])

        # Count by category
        categories = {"mandatory": 0, "optional": 0, "potential": 0}

        for incident in incidents:
            category = incident.get("category", "optional")
            if category in categories:
                categories[category] += 1

        # Count by file
        files: dict[str, int] = {}
        for incident in incidents:
            file_path = incident.get("uri", "unknown")
            files[file_path] = files.get(file_path, 0) + 1

        return {
            "total_incidents": len(incidents),
            "by_category": categories,
            "by_file": files,
            "files_with_issues": len(files),
            "timestamp": datetime.now().isoformat(),
        }

    def generate_json_report(self, report_data: dict[str, Any], output_path: Path | None = None) -> Path:
        """
        Generate JSON report.

        Args:
            report_data: Report data
            output_path: Output file path (auto-generated if None)

        Returns:
            Path to generated report
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            output_path = self.reports_dir / f"report-{timestamp}.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, default=str)

        logger.info("JSON report generated: %s", output_path)
        return output_path

    def generate_markdown_report(self, report_data: dict[str, Any], summary: dict[str, Any], output_path: Path | None = None) -> Path:
        """
        Generate Markdown report.

        Args:
            report_data: Report data
            summary: Summary statistics
            output_path: Output file path

        Returns:
            Path to generated report
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            output_path = self.reports_dir / f"report-{timestamp}.md"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "# YAML Validation Report",
            "",
            f"**Generated:** {summary['timestamp']}",
            "",
            "## Summary",
            "",
            f"- **Total Issues:** {summary['total_incidents']}",
            f"- **Mandatory:** {summary['by_category']['mandatory']}",
            f"- **Optional:** {summary['by_category']['optional']}",
            f"- **Potential:** {summary['by_category']['potential']}",
            f"- **Files with Issues:** {summary['files_with_issues']}",
            "",
            "## Issues by File",
            "",
        ]

        for file_path, count in sorted(summary["by_file"].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- `{file_path}`: {count} issues")

        lines.extend(["", "## Detailed Issues", ""])

        incidents = report_data.get("incidents", [])
        for incident in incidents:
            lines.extend(
                [
                    f"### {incident.get('ruleID', 'unknown')}",
                    "",
                    f"**File:** `{incident.get('uri', 'unknown')}`  ",
                    f"**Line:** {incident.get('lineNumber', '?')}  ",
                    f"**Category:** {incident.get('category', 'optional')}  ",
                    f"**Effort:** {incident.get('effort', '?')}",
                    "",
                    incident.get("message", "No message"),
                    "",
                ]
            )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info("Markdown report generated: %s", output_path)
        return output_path

    def create_report_metadata(self, execution_result: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
        """
        Create metadata for report.

        Args:
            execution_result: Kantra execution result
            summary: Report summary

        Returns:
            Metadata dictionary
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "status": execution_result.get("status"),
            "exit_code": execution_result.get("exit_code"),
            "command": execution_result.get("command"),
            "summary": summary,
            "version": "1.0.0",
        }

    def save_metadata(self, metadata: dict[str, Any], output_path: Path) -> None:
        """
        Save report metadata.

        Args:
            metadata: Metadata dictionary
            output_path: Output path
        """
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, default=str)

        logger.info("Metadata saved: %s", output_path)
