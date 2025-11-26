#!/usr/bin/env bash
# shellcheck source=scripts/bash/lib/speckit.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/speckit.sh"

main() {
    local docker_dir="$LIB_DIR/../../../docker"

    logger_info "Stopping Virtual Application Environment..."
    docker compose -f "$docker_dir/docker-compose.yml" down

    logger_info "Stopping Local Infrastructure..."
    docker compose -f "$docker_dir/docker-compose.infra.yml" down

    logger_success "All services stopped."
}

invoke_speckit_block "Stop-All" main "$@"
