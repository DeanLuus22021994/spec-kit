#!/usr/bin/env bash
# shellcheck source=lib/speckit.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/speckit.sh"

main() {
    local json_mode=false
    for arg in "$@"; do case "$arg" in --json) json_mode=true ;; --help|-h) echo "Usage: $0 [--json]"; exit 0 ;; esac; done

    get_feature_paths_env
    check_feature_branch "$CURRENT_BRANCH" || return 1

    mkdir -p "$FEATURE_DIR"
    local template="$REPO_ROOT/templates/plan-template.md"
    if [[ -f "$template" ]]; then
        cp "$template" "$IMPL_PLAN"
    fi

    if $json_mode; then
        printf '{"FEATURE_SPEC":"%s","IMPL_PLAN":"%s","SPECS_DIR":"%s","BRANCH":"%s"}\n' \
            "$FEATURE_SPEC" "$IMPL_PLAN" "$FEATURE_DIR" "$CURRENT_BRANCH"
    else
        logger_info "FEATURE_SPEC: $FEATURE_SPEC"
        logger_info "IMPL_PLAN: $IMPL_PLAN"
        logger_info "SPECS_DIR: $FEATURE_DIR"
        logger_info "BRANCH: $CURRENT_BRANCH"
    fi
}

invoke_speckit_block "Setup-Plan" main "$@"
