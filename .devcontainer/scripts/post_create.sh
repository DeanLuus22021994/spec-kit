#!/usr/bin/env bash
set -euo pipefail
source /opt/devcontainer/scripts/common.sh

log_info "Post-create started"

ensure_cmd git || exit 1
git_safe_dir "/workspaces/spec-kit"

# Prefer uv if available; fallback to python -m venv + pip
if command -v uv >/dev/null 2>&1; then
  log_info "Syncing Python environment via uv..."
  uv --version
  # Create a project-local venv at .venv
  uv venv --python 3.11 --seed .venv
  # Install project dependencies
  uv sync
else
  log_warn "uv not found; falling back to python venv + pip"
  python3 -m venv .venv
  source .venv/bin/activate
  python -m pip install --upgrade pip
  pip install -e ".[dev]" || pip install -r requirements.txt || true
fi

# Smoke test CLI
if [ -f "pyproject.toml" ]; then
  log_info "Verifying CLI entrypoint..."
  source .venv/bin/activate
  uv run specify --help >/dev/null 2>&1 || true
fi

log_info "Post-create completed"