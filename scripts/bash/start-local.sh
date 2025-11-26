#!/usr/bin/env bash
# shellcheck source=./lib/speckit.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/speckit.sh"

main() {
    local docker_dir="$LIB_DIR/../../../docker"

    logger_info "Starting Local Infrastructure (Database, Redis, Vector Store, GPU Services)..."
    docker compose -f "$docker_dir/docker-compose.infra.yml" up -d
    logger_success "Local Infrastructure is running."
}

invoke_speckit_block "Start-Local" main "$@"
