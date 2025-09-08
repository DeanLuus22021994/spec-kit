#!/usr/bin/env bash
set -euo pipefail

log() {
  local level="$1"; shift
  printf "[%s] %s\n" "$level" "$*"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error(){ log "ERROR" "$@"; }

ensure_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log_error "Missing required command: $1"
    return 1
  fi
}

git_safe_dir() {
  local dir="$1"
  if git config --global --get-all safe.directory | grep -q "^$dir$"; then
    return 0
  fi
  git config --global --add safe.directory "$dir"
}