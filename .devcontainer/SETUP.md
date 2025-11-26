# DevContainer Setup - Copilot-Optimized Python Environment

## Quick Start

**Prerequisites**:

- GitHub token with `repo`, `read:org`, `read:project` permissions
- Docker Desktop: 4GB+ RAM, 2+ CPU cores, 16GB+ storage

**Setup**:

```bash
# Set token (required for Copilot integration)
export GITHUB_TOKEN=ghp_your_token_here  # Linux/macOS
$env:GITHUB_TOKEN="ghp_your_token_here"  # Windows PowerShell

# Open in DevContainer
# VS Code → Command Palette → "Dev Containers: Reopen in Container"
```

**Validation**:

```bash
bash .devcontainer/scripts/validate.sh  # Should show 27/27 checks passed
```

Expected output: `27/27 checks passed`

## Python Development Environment

**Comprehensive toolchain** for AI-assisted Python development:

- **Formatters**: autopep8, black, yapf, ruff (primary)
- **Linters**: flake8, pylint, bandit, pycodestyle, pydocstyle
- **Type Checking**: mypy with strict mode
- **Testing**: pytest framework
- **Package Management**: pipenv, virtualenv, uv

**VS Code Extensions** (8 configured):

- `github.copilot` + `GitHub.copilot-chat` - AI assistance
- `ms-python.autopep8` - PEP 8 auto-formatting
- `ms-python.flake8` - Style enforcement
- `ms-python.black-formatter` - Code formatting
- `charliermarsh.ruff` - Fast linting/formatting (primary)

**Copilot Optimization**:

- Multi-formatter support for diverse coding styles
- Type safety enabled for better AI context
- Auto-format on save with import organization
- Comprehensive linting for enhanced suggestions

## Performance Features

**Container Optimizations**:

- 5 persistent cache volumes (node_modules, .venv, pip, npm, yarn)
- Build cache persistence across sessions
- Memory: 4GB+ recommended, CPU: 2+ cores
- Optimized Python compilation with shared libraries

**Development Workflow**:

- Auto-activation of Python virtual environment
- Shell integration for seamless tool access
- Performance monitoring and build statistics
- Fast container restarts via volume persistence

## Core Tools

- **GitHub Copilot**: AI code completion and chat
- **Python 3.11**: Optimized build with 13 development tools
- **Node.js LTS**: Package management with cache optimization
- **Ruff**: Primary formatter for speed and AI compatibility
- **Docker-in-Docker**: Container development support
- **GitHub CLI**: Repository automation
- **Git**: Performance-tuned configuration

## Troubleshooting

**Token Issues**: Set `GITHUB_TOKEN` before VS Code startup, restart if needed
**Build Issues**: `docker system prune -f` → Rebuild container via Command Palette
**Tool Missing**: Validation automatically installs missing Python tools
**Performance**: Check cache mounts active, verify 4GB+ memory allocation
