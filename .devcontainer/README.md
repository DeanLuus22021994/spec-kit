# Dev Container

This devcontainer provides a reproducible Python 3.11 environment with [uv](https://github.com/astral-sh/uv).

Key behaviors:
- Non-root user (`vscode`)
- uv preinstalled at build time
- Dependency sync via `post_create.sh` using your [pyproject](../pyproject.toml)
- Caches persisted via Docker volumes

Common commands:
- Rebuild container: Dev Containers: Rebuild and Reopen in Container
- Run CLI: `uv run specify --help`