#!/usr/bin/env bash

# Defensive Programming
set -euo pipefail

# Determine script directory for sourcing
LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load Modules
# shellcheck source=scripts/bash/lib/logger.sh
source "$LIB_DIR/logger.sh"
# shellcheck source=scripts/bash/lib/common.sh
source "$LIB_DIR/common.sh"

invoke_speckit_block() {
    local name="$1"
    shift
    local callback="$1"
    shift

    # Initialize Logger
    logger_init "$name"

    # Execute the callback with remaining arguments
    if ! "$callback" "$@"; then
        logger_error "Critical Error in $name"
        exit 1
    fi
}
