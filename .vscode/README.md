# VS Code Workspace Config

Optimized VS Code workspace for Copilot-driven development of Spec-Kit.

## Copilot Optimizations

This workspace is specifically configured for AI-assisted development:

**✅ Core Optimizations:**

- **GitHub Copilot** enabled for all languages with chat integration
- **Brief, C2-proficient** markdown templates and documentation
- **Streamlined extensions** - essential tools only, no conflicts
- **Performance-focused** file exclusions and search optimization
- **Human-in-the-loop** + AI development workflow ready

**✅ Key Features:**

- **Snippets**: Brief templates (markdown, Python, YAML)
- **Keybindings**: `Ctrl+I` (Copilot generate), `Ctrl+Shift+I` (Chat focus)
- **Settings**: Black formatter, .venv Python path, optimized exclusions
- **Tasks**: Core development tasks (setup, lint, format, MCP servers)
- **Debug**: Simplified CLI-focused debug profiles

## Structure

```
.vscode/
├── settings.json              # Workspace config
├── tasks.json                 # Build/test tasks
├── launch.json                # Debug profiles
├── extensions.json            # Required extensions
├── keybindings.json           # Custom shortcuts
├── config/workspace.json      # Multi-folder setup
├── snippets/*.code-snippets   # Language snippets
├── scripts/*.sh               # Automation scripts
├── commands/*.yaml            # Command definitions
└── docs/*.md                  # Dev documentation
```

## Quick Start

### 1. Install Extensions

Install recommended extensions when prompted:

- **GitHub Copilot** - AI code generation
- **Python** - Language support
- **Error Lens** - Inline diagnostics
- **GitLens** - Git integration

### 2. Python Environment

Pre-configured to use `.venv/bin/python` with Black formatter.

### 3. Development Workflow

- **Copilot**: `Ctrl+I` for code generation, `Ctrl+Shift+I` for chat
- **Tasks**: `Ctrl+Shift+P` → "Tasks: Run Task" for common operations
- **Debug**: `F5` to debug CLI commands

### 4. MCP Servers (Optional)

Enhanced AI assistance with context servers:

```bash
# Start development servers
.vscode/scripts/mcp-server.sh start development

# Stop servers
.vscode/scripts/mcp-server.sh stop
```

## Configuration Details

### Optimized Components

**Snippets Refined:**

- `markdown.code-snippets` - Brief, technical templates
- `python.code-snippets` - Minimal CLI-focused snippets
- `yaml.code-snippets` - Concise config templates

**Extensions Streamlined:**

- Prioritized GitHub Copilot & Copilot Chat
- Essential tools only (Ruff, Black, MyPy, Pylance, ErrorLens)
- Removed redundant/conflicting extensions

**Settings Configured:**

- Copilot enabled for all relevant languages
- Python environment pointing to `.venv`
- Black as default formatter
- Performance-focused file exclusions

**Tasks Simplified:**

- Core development tasks only
- MCP server management
- Build/test/lint commands

**Keybindings:**

- `Ctrl+I` - Copilot generate
- `Ctrl+Shift+I` - Copilot Chat focus
- Essential shortcuts only

## Available Tasks

Use `Ctrl+Shift+P` → "Tasks: Run Task":

- **Setup**: Initialize development environment
- **CLI Help**: Display CLI help
- **CLI Check**: Run system validation
- **Format**: Format code with Ruff
- **Lint**: Check code style with Ruff
- **Type Check**: Validate types with MyPy
- **MCP Start**: Start MCP development servers
- **MCP Stop**: Stop MCP servers

## Debugging

**Available Configurations:**

- **Debug CLI**: Debug CLI help command
- **Debug CLI - Check**: Debug system check
- **Debug Current Python File**: Debug active file
- **Attach to Python Process**: Attach to running process

**Usage:**

1. Set breakpoints (click in gutter)
2. Press `F5` or use Debug panel (`Ctrl+Shift+D`)
3. Select configuration and start debugging

## MCP Integration

Enhanced AI assistance with Model Context Protocol servers:

**Configured Servers:**

- **GitHub**: Repository management (requires `GITHUB_TOKEN`)
- **Filesystem**: File operations within workspace
- **Playwright**: Web automation (optional)

**Environment Setup:**

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

## Development Workflow

**Code Development:**

- Format on save enabled
- Auto-organize imports on save
- Use `Ctrl+I` for Copilot suggestions

**Testing:**

- Use VS Code tasks for CLI operations
- `F5` to debug with breakpoints
- GitLens for inline blame info

**AI Assistance:**

- GitHub Copilot for code generation
- MCP servers for enhanced context
- `Ctrl+Shift+I` for Copilot chat

## Troubleshooting

**Python Issues:**

- Ensure interpreter is set to `.venv/bin/python`
- Restart language server: `Ctrl+Shift+P` → "Python: Restart Language Server"

**MCP Server Issues:**

```bash
# Check server status
.vscode/scripts/mcp-server.sh status
```

**Docker Issues:**

```bash
# Verify Docker is running
docker info
```

## Best Practices

1. **AI-First Development**: Use Copilot for code generation, chat for complex logic
2. **Brief Documentation**: Keep markdown concise and technical
3. **Task-Based Workflow**: Use VS Code tasks instead of manual commands
4. **Performance Focus**: Leverage optimized file exclusions and caching
5. **Human-in-the-Loop**: Review and refine AI-generated code
