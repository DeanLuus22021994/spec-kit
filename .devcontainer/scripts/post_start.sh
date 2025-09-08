#!/usr/bin/env bash
set -euo pipefail
source /opt/devcontainer/scripts/common.sh

log_info "Post-start hook"
# Place lightweight, idempotent tasks here (e.g., update submodules if used)
# git submodule update --init --recursive || true