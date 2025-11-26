#!/usr/bin/env bash
# shellcheck source=lib/speckit.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/speckit.sh"

main() {
    local json_mode=false
    for arg in "$@"; do case "$arg" in --json) json_mode=true ;; --help|-h) echo "Usage: $0 [--json]"; exit 0 ;; esac; done

    get_feature_paths_env
    check_feature_branch "$CURRENT_BRANCH" || return 1

    if [[ ! -d "$FEATURE_DIR" ]]; then
        logger_error "Feature directory not found: $FEATURE_DIR"
        logger_info "Run /specify first."
        return 1
    fi
    if [[ ! -f "$IMPL_PLAN" ]]; then
        logger_error "plan.md not found in $FEATURE_DIR"
        logger_info "Run /plan first."
        return 1
    fi

    if $json_mode; then
        local docs=()
        [[ -f "$RESEARCH" ]] && docs+=("research.md")
        [[ -f "$DATA_MODEL" ]] && docs+=("data-model.md")
        if [[ -d "$CONTRACTS_DIR" ]] && [[ -n "$(ls -A "$CONTRACTS_DIR" 2>/dev/null)" ]]; then docs+=("contracts/"); fi
        [[ -f "$QUICKSTART" ]] && docs+=("quickstart.md")

        local json_docs
        json_docs=$(printf '"%s",' "${docs[@]}")
        json_docs="[${json_docs%,}]"
        printf '{"FEATURE_DIR":"%s","AVAILABLE_DOCS":%s}\n' "$FEATURE_DIR" "$json_docs"
    else
        logger_info "FEATURE_DIR:$FEATURE_DIR"
        logger_info "AVAILABLE_DOCS:"
        check_file_exists "$RESEARCH" "research.md"
        check_file_exists "$DATA_MODEL" "data-model.md"
        check_dir_has_files "$CONTRACTS_DIR" "contracts/"
        check_file_exists "$QUICKSTART" "quickstart.md"
    fi
}

invoke_speckit_block "Check-Task-Prereqs" main "$@"
