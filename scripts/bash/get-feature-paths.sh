#!/usr/bin/env bash
# shellcheck source=./lib/speckit.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/speckit.sh"

main() {
    get_feature_paths_env
    check_feature_branch "$CURRENT_BRANCH" || return 1

    logger_info "REPO_ROOT: $REPO_ROOT"
    logger_info "BRANCH: $CURRENT_BRANCH"
    logger_info "FEATURE_DIR: $FEATURE_DIR"
    logger_info "FEATURE_SPEC: $FEATURE_SPEC"
    logger_info "IMPL_PLAN: $IMPL_PLAN"
    logger_info "TASKS: $TASKS"
}

invoke_speckit_block "Get-Feature-Paths" main "$@"
