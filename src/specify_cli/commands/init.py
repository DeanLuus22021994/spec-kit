"""Init command handler."""

from __future__ import annotations

import os
import shlex
import shutil
import ssl
import sys
from pathlib import Path

import httpx
import truststore
import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel

from specify_cli.config import AGENT_CONFIG, COMMANDS_INIT_YAML, SCRIPT_TYPE_CHOICES
from specify_cli.git import init_git_repo, is_git_repo
from specify_cli.template import (
    download_and_extract_template,
    ensure_executable_scripts,
)
from specify_cli.ui import StepTracker, select_with_arrows, show_banner
from specify_cli.utils import check_tool

console = Console()

ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)


def init(
    project_name: str | None = None,
    ai_assistant: str | None = None,
    script_type: str | None = None,
    ignore_agent_tools: bool = False,
    no_git: bool = False,
    here: bool = False,
    force: bool = False,
    skip_tls: bool = False,
    debug: bool = False,
    github_token: str | None = None,
) -> None:
    """
    Initialize a new Specify project from the latest template.
    """
    messages = COMMANDS_INIT_YAML.get("messages", {})
    errors = messages.get("errors", {})
    warnings = messages.get("warnings", {})
    prompts = messages.get("prompts", {})
    status = messages.get("status", {})
    steps = messages.get("steps", {})

    show_banner()

    if project_name == ".":
        here = True
        project_name = None  # Clear project_name to use existing validation logic

    if here and project_name:
        console.print(
            f"[red]Error:[/red] {errors.get('conflict_here_project', 'Cannot specify both project name and --here flag')}"
        )
        raise typer.Exit(1)

    if not here and not project_name:
        msg = errors.get(
            "missing_target",
            "Must specify either a project name, use '.' for current directory, or use --here flag",
        )
        console.print(f"[red]Error:[/red] {msg}")
        raise typer.Exit(1)

    if here:
        project_name = Path.cwd().name
        project_path = Path.cwd()

        existing_items = list(project_path.iterdir())
        if existing_items:
            console.print(
                f"[yellow]Warning:[/yellow] {warnings.get('dir_not_empty', 'Current directory is not empty').format(count=len(existing_items))}"
            )
            msg = warnings.get(
                "merge_warning",
                "Template files will be merged with existing content and may overwrite existing files",
            )
            console.print(f"[yellow]{msg}[/yellow]")
            if force:
                console.print(
                    status.get(
                        "force_skip",
                        "[cyan]--force supplied: skipping confirmation and proceeding with merge[/cyan]",
                    )
                )
            else:
                response = typer.confirm(
                    prompts.get("continue_merge", "Do you want to continue?")
                )
                if not response:
                    console.print(
                        f"[yellow]{status.get('cancelled', 'Operation cancelled')}[/yellow]"
                    )
                    raise typer.Exit(0)
    else:
        if project_name is None:
            # Should be unreachable due to earlier checks
            raise typer.Exit(1)
        project_path = Path(project_name).resolve()
        if project_path.exists():
            error_msg = errors.get(
                "directory_exists", "Directory '{project_name}' already exists"
            ).format(project_name=project_name)
            error_panel = Panel(
                error_msg,
                title="[red]Directory Conflict[/red]",
                border_style="red",
                padding=(1, 2),
            )
            console.print()
            console.print(error_panel)
            raise typer.Exit(1)

    current_dir = Path.cwd()

    setup_lines = [
        f"[cyan]{status.get('setup_title', 'Specify Project Setup')}[/cyan]",
        "",
        f"{'Project':<15} [green]{project_path.name}[/green]",
        f"{'Working Path':<15} [dim]{current_dir}[/dim]",
    ]

    if not here:
        setup_lines.append(f"{'Target Path':<15} [dim]{project_path}[/dim]")

    console.print(Panel("\n".join(setup_lines), border_style="cyan", padding=(1, 2)))

    should_init_git = False
    if not no_git:
        should_init_git = bool(check_tool("git"))
        if not should_init_git:
            console.print(
                f"[yellow]{warnings.get('git_not_found', 'Git not found - will skip repository initialization')}[/yellow]"
            )

    if ai_assistant:
        if ai_assistant not in AGENT_CONFIG:
            msg = errors.get("invalid_ai", "Invalid AI assistant").format(
                ai_assistant=ai_assistant, choices=", ".join(AGENT_CONFIG.keys())
            )
            console.print(f"[red]Error:[/red] {msg}")
            raise typer.Exit(1)
        selected_ai = ai_assistant
    else:
        # Create options dict for selection (agent_key: display_name)
        ai_choices = {key: config["name"] for key, config in AGENT_CONFIG.items()}
        selected_ai = select_with_arrows(
            ai_choices, prompts.get("choose_ai", "Choose your AI assistant:"), "copilot"
        )

    if not ignore_agent_tools:
        agent_config = AGENT_CONFIG.get(selected_ai)
        if agent_config and agent_config["requires_cli"]:
            install_url = agent_config["install_url"]
            if not check_tool(selected_ai):
                error_msg = errors.get("agent_not_found", "{agent} not found").format(
                    agent=selected_ai, url=install_url, name=agent_config["name"]
                )
                error_panel = Panel(
                    error_msg,
                    title="[red]Agent Detection Error[/red]",
                    border_style="red",
                    padding=(1, 2),
                )
                console.print()
                console.print(error_panel)
                raise typer.Exit(1)

    if script_type:
        if script_type not in SCRIPT_TYPE_CHOICES:
            msg = errors.get("invalid_script", "Invalid script type").format(
                script_type=script_type, choices=", ".join(SCRIPT_TYPE_CHOICES.keys())
            )
            console.print(f"[red]Error:[/red] {msg}")
            raise typer.Exit(1)
        selected_script = script_type
    else:
        default_script = "ps" if os.name == "nt" else "sh"

        if sys.stdin.isatty():
            selected_script = select_with_arrows(
                SCRIPT_TYPE_CHOICES,
                prompts.get("choose_script", "Choose script type (or press Enter)"),
                default_script,
            )
        else:
            selected_script = default_script

    console.print(
        f"[cyan]{status.get('selected_ai', 'Selected AI assistant:')}[/cyan] {selected_ai}"
    )
    console.print(
        f"[cyan]{status.get('selected_script', 'Selected script type:')}[/cyan] {selected_script}"
    )

    tracker = StepTracker("Initialize Specify Project")

    sys._specify_tracker_active = True  # type: ignore # pylint: disable=protected-access

    tracker.add("precheck", "Check required tools")
    tracker.complete("precheck", "ok")
    tracker.add("ai-select", "Select AI assistant")
    tracker.complete("ai-select", f"{selected_ai}")
    tracker.add("script-select", "Select script type")
    tracker.complete("script-select", selected_script)
    for key, label in [
        ("fetch", "Fetch latest release"),
        ("download", "Download template"),
        ("extract", "Extract template"),
        ("zip-list", "Archive contents"),
        ("extracted-summary", "Extraction summary"),
        ("chmod", "Ensure scripts executable"),
        ("cleanup", "Cleanup"),
        ("git", "Initialize git repository"),
        ("final", "Finalize"),
    ]:
        tracker.add(key, label)

    # Track git error message outside Live context so it persists
    git_error_message = None

    with Live(
        tracker.render(), console=console, refresh_per_second=8, transient=True
    ) as live:
        tracker.attach_refresh(lambda: live.update(tracker.render()))
        try:
            verify = not skip_tls
            local_ssl_context = ssl_context if verify else False
            local_client = httpx.Client(verify=local_ssl_context)

            download_and_extract_template(
                project_path,
                selected_ai,
                selected_script,
                here,
                verbose=False,
                tracker=tracker,
                http_client=local_client,
                debug=debug,
                github_token=github_token,
            )

            ensure_executable_scripts(project_path, tracker=tracker)

            if not no_git:
                tracker.start("git")
                if is_git_repo(project_path):
                    tracker.complete("git", "existing repo detected")
                elif should_init_git:
                    success, error_msg = init_git_repo(project_path, quiet=True)
                    if success:
                        tracker.complete("git", "initialized")
                    else:
                        tracker.error("git", "init failed")
                        git_error_message = error_msg
                else:
                    tracker.skip("git", "git not available")
            else:
                tracker.skip("git", "--no-git flag")

            tracker.complete("final", "project ready")
        except Exception as e:
            tracker.error("final", str(e))
            console.print(
                Panel(
                    f"Initialization failed: {e}", title="Failure", border_style="red"
                )
            )
            if debug:
                _env_pairs = [
                    ("Python", sys.version.split()[0]),
                    ("Platform", sys.platform),
                    ("CWD", str(Path.cwd())),
                ]
                _label_width = max(len(k) for k, _ in _env_pairs)
                env_lines = [
                    f"{k.ljust(_label_width)} → [bright_black]{v}[/bright_black]"
                    for k, v in _env_pairs
                ]
                console.print(
                    Panel(
                        "\n".join(env_lines),
                        title="Debug Environment",
                        border_style="magenta",
                    )
                )
            if not here and project_path.exists():
                shutil.rmtree(project_path)
            raise typer.Exit(1) from e
        finally:
            pass

    console.print(tracker.render())
    console.print("\n[bold green]Project ready.[/bold green]")

    # Show git error details if initialization failed
    if git_error_message:
        console.print()
        msg = warnings.get(
            "git_init_failed",
            "Git repository initialization failed\n\n{error}\n\n"
            "[dim]You can initialize git manually later with:[/dim]\n"
            "[cyan]cd {path}[/cyan]\n[cyan]git init[/cyan]\n"
            "[cyan]git add .[/cyan]\n"
            '[cyan]git commit -m "Initial commit"[/cyan]',
        ).format(error=git_error_message, path=project_path if not here else ".")
        git_error_panel = Panel(
            msg,
            title="[red]Git Initialization Failed[/red]",
            border_style="red",
            padding=(1, 2),
        )
        console.print(git_error_panel)

    # Agent folder security notice
    agent_config = AGENT_CONFIG.get(selected_ai)
    if agent_config:
        agent_folder = agent_config["folder"]
        msg = status.get(
            "agent_security_body",
            "Some agents may store credentials, auth tokens, or other identifying and private artifacts in the agent folder within your project.\n"
            "Consider adding [cyan]{folder}[/cyan] (or parts of it) to [cyan].gitignore[/cyan] to prevent accidental credential leakage.",
        ).format(folder=agent_folder)
        security_notice = Panel(
            msg,
            title=f"[yellow]{status.get('agent_security_title', 'Agent Folder Security')}[/yellow]",
            border_style="yellow",
            padding=(1, 2),
        )
        console.print()
        console.print(security_notice)

    steps_lines = []
    if not here:
        steps_lines.append(
            steps.get(
                "cd_project",
                "1. Go to the project folder: [cyan]cd {project_name}[/cyan]",
            ).format(project_name=project_name)
        )
        step_num = 2
    else:
        steps_lines.append(
            steps.get("already_here", "1. You're already in the project directory!")
        )
        step_num = 2

    # Add Codex-specific setup step if needed
    if selected_ai == "codex":
        codex_path = project_path / ".codex"
        quoted_path = shlex.quote(str(codex_path))
        if os.name == "nt":  # Windows
            cmd = f"setx CODEX_HOME {quoted_path}"
        else:  # Unix-like systems
            cmd = f"export CODEX_HOME={quoted_path}"

        steps_lines.append(
            steps.get(
                "codex_home",
                "{step_num}. Set [cyan]CODEX_HOME[/cyan] environment variable before running Codex: [cyan]{cmd}[/cyan]",
            ).format(step_num=step_num, cmd=cmd)
        )
        step_num += 1

    next_steps_header = (
        COMMANDS_INIT_YAML.get("messages", {})
        .get("next_steps", {})
        .get("header", "Start using slash commands with your AI agent:")
    )
    steps_lines.append(f"{step_num}. {next_steps_header}")

    next_steps_items = (
        COMMANDS_INIT_YAML.get("messages", {}).get("next_steps", {}).get("items", [])
    )
    for item in next_steps_items:
        steps_lines.append(f"   {item}")

    steps_panel = Panel(
        "\n".join(steps_lines), title="Next Steps", border_style="cyan", padding=(1, 2)
    )
    console.print()
    console.print(steps_panel)

    enhancement_header = (
        COMMANDS_INIT_YAML.get("messages", {}).get("enhancements", {}).get("header", "")
    )
    enhancement_items = (
        COMMANDS_INIT_YAML.get("messages", {}).get("enhancements", {}).get("items", [])
    )

    if enhancement_header and enhancement_items:
        enhancement_lines = [
            enhancement_header,
            "",
        ]
        enhancement_lines.extend(enhancement_items)

        enhancements_panel = Panel(
            "\n".join(enhancement_lines),
            title="Enhancement Commands",
            border_style="cyan",
            padding=(1, 2),
        )
        console.print()
        console.print(enhancements_panel)
