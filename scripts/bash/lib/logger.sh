#!/usr/bin/env bash

# Logger Functions

LOG_CONTEXT="SpecKit"

logger_init() {
    LOG_CONTEXT="$1"
}

logger_info() {
    echo "[INFO] [$LOG_CONTEXT] $1"
}

logger_success() {
    echo "[SUCCESS] [$LOG_CONTEXT] $1"
}

logger_warn() {
    echo "[WARN] [$LOG_CONTEXT] $1" >&2
}

logger_error() {
    echo "[ERROR] [$LOG_CONTEXT] $1" >&2
}
