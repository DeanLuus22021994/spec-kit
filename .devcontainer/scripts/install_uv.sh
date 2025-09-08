#!/usr/bin/env bash
set -euo pipefail
source /opt/devcontainer/scripts/common.sh

if command -v uv >/dev/null 2>&1; then
  log_info "uv already installed: $(uv --version)"
  exit 0
fi

log_info "Installing uv..."
# Official installer
curl -fsSL https://astral.sh/uv/install.sh | sh

# Ensure available on PATH for the current user
if ! command -v uv >/dev/null 2>&1; then
  export PATH="$HOME/.local/bin:$PATH"
fi
log_info "uv installed: $(uv --version)"