"""Check command handler."""

from __future__ import annotations

import json

from rich.console import Console

from specify_cli.config import AGENT_CONFIG, SETTINGS_YAML
from specify_cli.ui import StepTracker, show_banner
from specify_cli.utils import check_tool

console = Console()


def check(json_output: bool = False, verbose: bool = False) -> None:
    """Check that all required tools are installed."""
    if not json_output:
        show_banner()
        console.print("[bold]Checking for installed tools...[/bold]\n")

    tracker = StepTracker("Check Available Tools") if not json_output else None

    results = {}

    # Check Git
    if tracker:
        tracker.add("git", "Git version control")
    git_path = check_tool("git", tracker=tracker)
    results["git"] = git_path

    # Check Agents
    for agent_key, agent_config in AGENT_CONFIG.items():
        agent_name = agent_config["name"]
        requires_cli = agent_config["requires_cli"]

        if tracker:
            tracker.add(agent_key, agent_name)

        if requires_cli:
            path = check_tool(agent_key, tracker=tracker)
            results[agent_key] = path
        else:
            # IDE-based agent - skip CLI check and mark as optional
            if tracker:
                tracker.skip(agent_key, "IDE-based, no CLI check")
            # Don't count IDE agents as "found"
            results[agent_key] = None

    # Check Optional Tools from Settings
    optional_tools = SETTINGS_YAML.get("optional_tools", {})
    for tool_key, tool_name in optional_tools.items():
        if tracker:
            tracker.add(tool_key, tool_name)
        path = check_tool(tool_key, tracker=tracker)
        results[tool_key] = path

    if json_output:
        console.print(json.dumps(results, indent=2))
        return

    if tracker:
        console.print(tracker.render())

    if verbose:
        console.print("\n[bold]Tool Paths:[/bold]")
        for tool, path in results.items():
            status = f"[green]{path}[/green]" if path else "[red]Not found[/red]"
            console.print(f"  {tool:<20} {status}")

    console.print("\n[bold green]Specify CLI is ready to use![/bold green]")

    if not results.get("git"):
        console.print("[dim]Tip: Install git for repository management[/dim]")

    # Check if any agent is found (excluding IDE agents which are None but not strictly "missing" in this context,
    # but we want to know if at least one CLI agent is available or if the user has an IDE agent configured?
    # The original logic was `if not any(agent_results.values())`.
    # Here results values are paths (truthy) or None (falsy).
    if not any(results.values()):
        console.print("[dim]Tip: Install an AI assistant for the best experience[/dim]")
