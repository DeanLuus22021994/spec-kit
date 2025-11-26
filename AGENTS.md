# AGENTS.md

## About Spec Kit and Specify

**GitHub Spec Kit** implements Spec-Driven Development (SDD). **Specify CLI** bootstraps projects with the Spec Kit framework, supporting multiple AI agents.

## Adding New Agent Support

### 1. Register Agent in `src/specify_cli/config/agents.yaml`

**CRITICAL**: Use the **actual CLI executable name** as the key (e.g., `cursor-agent`, not `cursor`).

```yaml
cursor-agent:
  name: "Cursor"
  folder: ".cursor/commands/"
  install_url: "https://cursor.sh"
  requires_cli: true  # Set false for IDE-based agents (e.g. Copilot)
```

### 2. Define Commands in `src/specify_cli/config/agent_commands.yaml`

Define metadata, scripts, and handoffs.

```yaml
new-command:
  description: "Command description"
  scripts:
    sh: scripts/bash/new-command.sh
    ps: scripts/powershell/new-command.ps1
```

### 3. Create Command Templates

Create Markdown templates in `.specify/templates/commands/`. Use `{SCRIPT}` and `$ARGUMENTS` placeholders.

### 4. Update CLI & Scripts

1.  **CLI Help**: Update `--ai` help text in `src/specify_cli/commands/init.py`.
2.  **Release Script**: Add agent to `ALL_AGENTS` and case statement in `.github/workflows/scripts/create-release-packages.sh`.
3.  **GitHub Release**: Add packages to `.github/workflows/scripts/create-github-release.sh`.
4.  **Context Scripts**: Update `scripts/bash/update-agent-context.sh` and `scripts/powershell/update-agent-context.ps1` to handle the new agent's context file.

### 5. Update Documentation

1.  **README.md**: Add to "Prerequisites" or supported agents list.
2.  **Devcontainer**: Update `.devcontainer/devcontainer.json` (extensions) or `.devcontainer/post-create.sh` (CLI tools).

## Conventions

*   **Directories**: `.agent-name/commands/` (CLI) or IDE-specific (e.g., `.github/agents/`).
*   **Arguments**: `$ARGUMENTS` (Markdown), `{{args}}` (TOML).
*   **Placeholders**: `{SCRIPT}` (script path), `__AGENT__` (agent name).

## Testing

1.  Build packages: `./.github/workflows/scripts/create-release-packages.sh v1.0.0`
2.  Test init: `specify init --ai <agent>`
3.  Verify file generation and command execution.
