#!/usr/bin/env bash
#!/usr/bin/env bash
# shellcheck source=./lib/speckit.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/speckit.sh"
# shellcheck source=./lib/plan_utils.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/plan_utils.sh"
# shellcheck source=./lib/agent_updater.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/agent_updater.sh"

main() {
    local agent_type="${1:-}"

    get_feature_paths_env
    check_feature_branch "$CURRENT_BRANCH" || return 1

    local new_plan="$FEATURE_DIR/$PLAN_FILE_NAME"
    if ! parse_plan_data "$new_plan"; then return 1; fi

    local success=true

    if [[ -n "$agent_type" ]]; then
        if [[ -n "${SPECKIT_AGENTS_FILES[$agent_type]}" ]]; then
            update_agent_file "${SPECKIT_AGENTS_FILES[$agent_type]}" "${SPECKIT_AGENTS_NAMES[$agent_type]}" || success=false
        else
            logger_error "Unknown agent type '$agent_type'"
            return 1
        fi
    else
        local found_agent=false
        for type in "${!SPECKIT_AGENTS_FILES[@]}"; do
            if [[ -f "${SPECKIT_AGENTS_FILES[$type]}" ]]; then
                update_agent_file "${SPECKIT_AGENTS_FILES[$type]}" "${SPECKIT_AGENTS_NAMES[$type]}" || success=false
                found_agent=true
            fi
        done
        if [[ "$found_agent" == false ]]; then
            logger_info "No existing agent files found, creating default Claude file..."
            update_agent_file "${SPECKIT_AGENTS_FILES[claude]}" "${SPECKIT_AGENTS_NAMES[claude]}" || success=false
        fi
    fi

    logger_info "Summary of changes:"
    if [[ -n "$NEW_LANG" ]]; then echo "  - Added language: $NEW_LANG"; fi
    if [[ -n "$NEW_FRAMEWORK" ]]; then echo "  - Added framework: $NEW_FRAMEWORK"; fi
    if [[ -n "$NEW_DB" ]] && [[ "$NEW_DB" != "N/A" ]]; then echo "  - Added database: $NEW_DB"; fi

    if [[ "$success" == true ]]; then logger_success "Agent context update completed successfully"; else return 1; fi
}

invoke_speckit_block "Update-Agent-Context" main "$@"

