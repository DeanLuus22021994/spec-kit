#!/usr/bin/env python3
"""Report Command.

Generate validation reports.
"""

from __future__ import annotations

import json
import logging
import traceback
from datetime import datetime
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def generate_report(
    output_format: str,
    output_path: Path | None,
    include_coverage: bool,
    include_trends: bool,
    verbose: bool,
) -> int:
    """Generate validation report.

    Args:
        output_format: Report format (text, json, yaml, html, markdown).
        output_path: Output file path.
        include_coverage: Include coverage analysis.
        include_trends: Include historical trends.
        verbose: Verbose output.

    Returns:
        Exit code.
    """
    try:
        logger.info("Generating %s report", output_format)

        # Collect report data
        report_data = collect_report_data(include_coverage, include_trends)

        # Generate report in requested format
        if output_format == "text":
            report_content = generate_text_report(report_data)
        elif output_format == "json":
            report_content = generate_json_report(report_data)
        elif output_format == "yaml":
            report_content = generate_yaml_report(report_data)
        elif output_format == "html":
            report_content = generate_html_report(report_data)
        elif output_format == "markdown":
            report_content = generate_markdown_report(report_data)
        else:
            logger.error("Unsupported format: %s", output_format)
            return 1

        # Output report
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report_content, encoding="utf-8")
            logger.info("Report saved to: %s", output_path)
        else:
            print(report_content)

        return 0

    except (OSError, ValueError, yaml.YAMLError) as e:
        logger.error("Report generation failed: %s", e)
        if verbose:
            traceback.print_exc()
        return 1


def collect_report_data(include_coverage: bool, include_trends: bool) -> dict:
    """Collect data for report.

    Args:
        include_coverage: Include coverage analysis in report.
        include_trends: Include historical trends in report.

    Returns:
        Dictionary containing report data.
    """
    data: dict = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_rules": 0,
            "total_packages": 0,
            "total_profiles": 0,
        },
    }

    # Count rules and packages
    project_root = Path(__file__).parent.parent.parent.parent
    packages_dir = project_root / "tools" / ".config" / "validation" / "packages"

    if packages_dir.exists():
        packages = [d for d in packages_dir.iterdir() if d.is_dir()]
        data["summary"]["total_packages"] = len(packages)

        total_rules = 0
        for package_dir in packages:
            rules_dir = package_dir / "rules"
            if rules_dir.exists():
                total_rules += len(list(rules_dir.glob("*.yaml")))

        data["summary"]["total_rules"] = total_rules

    # Count profiles
    profiles_dir = project_root / "tools" / ".config" / "validation" / "profiles"
    if profiles_dir.exists():
        data["summary"]["total_profiles"] = len(list(profiles_dir.glob("*.yaml")))

    # Add coverage if requested
    if include_coverage:
        data["coverage"] = {
            "rule_coverage": "TBD",
            "best_practice_coverage": "TBD",
        }

    # Add trends if requested
    if include_trends:
        data["trends"] = {"message": "Historical trends not yet implemented"}

    return data


def generate_text_report(data: dict) -> str:
    """Generate text format report.

    Args:
        data: Report data dictionary.

    Returns:
        Formatted text report string.
    """
    lines = []
    lines.append("=" * 60)
    lines.append("YAML VALIDATION REPORT")
    lines.append("=" * 60)
    lines.append(f"\nGenerated: {data['timestamp']}")
    lines.append("\nSummary:")
    lines.append(f"  Total Rules:    {data['summary']['total_rules']}")
    lines.append(f"  Total Packages: {data['summary']['total_packages']}")
    lines.append(f"  Total Profiles: {data['summary']['total_profiles']}")

    if "coverage" in data:
        lines.append("\nCoverage:")
        lines.append(f"  Rule Coverage: {data['coverage']['rule_coverage']}")
        lines.append(f"  Best Practice Coverage: {data['coverage']['best_practice_coverage']}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def generate_json_report(data: dict) -> str:
    """Generate JSON format report.

    Args:
        data: Report data dictionary.

    Returns:
        JSON formatted string.
    """
    return json.dumps(data, indent=2)


def generate_yaml_report(data: dict) -> str:
    """Generate YAML format report.

    Args:
        data: Report data dictionary.

    Returns:
        YAML formatted string.
    """
    return yaml.dump(data, default_flow_style=False, sort_keys=False)


def generate_html_report(data: dict) -> str:
    """Generate HTML format report.

    Args:
        data: Report data dictionary.

    Returns:
        HTML formatted string.
    """
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>YAML Validation Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 48px;
            font-weight: bold;
            color: #3498db;
        }}
        .stat-label {{
            color: #7f8c8d;
            font-size: 14px;
            text-transform: uppercase;
            margin-top: 10px;
        }}
        .timestamp {{
            color: #95a5a6;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>YAML Validation Report</h1>
        <p class="timestamp">Generated: {data['timestamp']}</p>

        <div class="summary">
            <div class="stat-card">
                <div class="stat-number">{data['summary']['total_rules']}</div>
                <div class="stat-label">Total Rules</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{data['summary']['total_packages']}</div>
                <div class="stat-label">Total Packages</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{data['summary']['total_profiles']}</div>
                <div class="stat-label">Total Profiles</div>
            </div>
        </div>
    </div>
</body>
</html>
"""
    return html


def generate_markdown_report(data: dict) -> str:
    """Generate Markdown format report.

    Args:
        data: Report data dictionary.

    Returns:
        Markdown formatted string.
    """
    lines = []
    lines.append("# YAML Validation Report")
    lines.append(f"\n*Generated: {data['timestamp']}*")
    lines.append("\n## Summary")
    lines.append(f"\n- **Total Rules:** {data['summary']['total_rules']}")
    lines.append(f"- **Total Packages:** {data['summary']['total_packages']}")
    lines.append(f"- **Total Profiles:** {data['summary']['total_profiles']}")

    if "coverage" in data:
        lines.append("\n## Coverage")
        lines.append(f"\n- **Rule Coverage:** {data['coverage']['rule_coverage']}")
        lines.append(f"- **Best Practice Coverage:** {data['coverage']['best_practice_coverage']}")

    return "\n".join(lines)
