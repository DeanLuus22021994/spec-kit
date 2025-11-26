#!/usr/bin/env bash
# shellcheck source=scripts/bash/lib/speckit.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/speckit.sh"

main() {
    local docker_dir="$LIB_DIR/../../../docker"

    logger_info "Starting Virtual Application Environment (Backend, Engine, Frontend)..."
    docker compose -f "$docker_dir/docker-compose.yml" up -d
    logger_success "Virtual Application is running."
}

invoke_speckit_block "Start-Virtual" main "$@"
