#!/usr/bin/env bash
# shellcheck source=scripts/bash/lib/speckit.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/speckit.sh"

# Global variables for parsed plan data
NEW_LANG=""
NEW_FRAMEWORK=""
NEW_DB=""
NEW_PROJECT_TYPE=""

extract_plan_field() {
    local field_pattern="$1"
    local plan_file="$2"

    grep "^**${field_pattern}**: " "$plan_file" 2>/dev/null | \
        head -1 | \
        sed "s/^**${field_pattern}**: //" | \
        grep -v "NEEDS CLARIFICATION" | \
        grep -v "^N/A$" || echo ""
}

parse_plan_data() {
    local plan_file="$1"

    if [[ ! -f "$plan_file" ]]; then
        logger_error "Plan file not found: $plan_file"
        return 1
    fi

    if [[ ! -r "$plan_file" ]]; then
        logger_error "Plan file is not readable: $plan_file"
        return 1
    fi

    logger_info "Parsing plan data from $plan_file"

    NEW_LANG=$(extract_plan_field "Language/Version" "$plan_file")
    NEW_FRAMEWORK=$(extract_plan_field "Primary Dependencies" "$plan_file")
    NEW_DB=$(extract_plan_field "Storage" "$plan_file")
    NEW_PROJECT_TYPE=$(extract_plan_field "Project Type" "$plan_file")

    if [[ -n "$NEW_LANG" ]]; then logger_info "Found language: $NEW_LANG"; else logger_warn "No language information found in plan"; fi
    if [[ -n "$NEW_FRAMEWORK" ]]; then logger_info "Found framework: $NEW_FRAMEWORK"; fi
    if [[ -n "$NEW_DB" ]] && [[ "$NEW_DB" != "N/A" ]]; then logger_info "Found database: $NEW_DB"; fi
    if [[ -n "$NEW_PROJECT_TYPE" ]]; then logger_info "Found project type: $NEW_PROJECT_TYPE"; fi
}

get_project_structure() {
    local project_type="$1"
    if [[ "$project_type" == *"web"* ]]; then echo "backend/
frontend/
tests/"; else echo "src/
tests/"; fi
}

get_commands_for_language() {
    local lang="$1"
    case "$lang" in
        *"Python"*) echo "cd src && pytest && ruff check ." ;;
        *"Rust"*) echo "cargo test && cargo clippy" ;;
        *"JavaScript"*|*"TypeScript"*) echo "npm test && npm run lint" ;;
        *) echo "# Add commands for $lang" ;;
    esac
}

get_language_conventions() {
    local lang="$1"
    echo "$lang: Follow standard conventions"
}

create_new_agent_file() {
    local target_file="$1"
    local temp_file="$2"
    local project_name="$3"
    local current_date="$4"

    local template_file="$REPO_ROOT/$TEMPLATES_DIR_NAME/$AGENT_TEMPLATE_NAME"

    if [[ ! -f "$template_file" ]]; then
        logger_error "Template not found at $template_file"
        return 1
    fi

    logger_info "Creating new agent context file from template..."
    cp "$template_file" "$temp_file" || return 1

    local project_structure
    project_structure=$(get_project_structure "$NEW_PROJECT_TYPE")
    local commands
    commands=$(get_commands_for_language "$NEW_LANG")
    local language_conventions
    language_conventions=$(get_language_conventions "$NEW_LANG")

    local substitutions=(
        "s/\[PROJECT NAME\]/$project_name/"
        "s/\[DATE\]/$current_date/"
        "s/\[EXTRACTED FROM ALL PLAN.MD FILES\]/- $NEW_LANG + $NEW_FRAMEWORK ($CURRENT_BRANCH)/"
        "s|\[ACTUAL STRUCTURE FROM PLANS\]|$project_structure|"
        "s|\[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES\]|$commands|"
        "s|\[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE\]|$language_conventions|"
        "s|\[LAST 3 FEATURES AND WHAT THEY ADDED\]|- $CURRENT_BRANCH: Added $NEW_LANG + $NEW_FRAMEWORK|"
    )

    for substitution in "${substitutions[@]}"; do
        sed -i.bak "$substitution" "$temp_file" || return 1
    done
    rm -f "$temp_file.bak"
    return 0
}

update_active_technologies() {
    local target_file="$1"
    local temp_file="$2"
    local tech_section_start
    tech_section_start=$(grep -n "## Active Technologies" "$target_file" | cut -d: -f1)

    if [[ -z "$tech_section_start" ]]; then cp "$target_file" "$temp_file"; return 0; fi

    local tech_section_end
    tech_section_end=$(tail -n +$((tech_section_start + 1)) "$target_file" | grep -n "^## \|^$" | head -1 | cut -d: -f1)
    if [[ -n "$tech_section_end" ]]; then tech_section_end=$((tech_section_start + tech_section_end)); else tech_section_end=$(wc -l < "$target_file"); fi

    local existing_tech
    existing_tech=$(sed -n "${tech_section_start},${tech_section_end}p" "$target_file")
    local additions=()
    if [[ -n "$NEW_LANG" ]] && ! echo "$existing_tech" | grep -q "$NEW_LANG"; then additions+=("- $NEW_LANG + $NEW_FRAMEWORK ($CURRENT_BRANCH)"); fi
    if [[ -n "$NEW_DB" ]] && [[ "$NEW_DB" != "N/A" ]] && ! echo "$existing_tech" | grep -q "$NEW_DB"; then additions+=("- $NEW_DB ($CURRENT_BRANCH)"); fi

    if [[ ${#additions[@]} -gt 0 ]]; then
        {
            head -n $((tech_section_start)) "$target_file"
            sed -n "$((tech_section_start + 1)),$((tech_section_end - 1))p" "$target_file"
            printf '%s\n' "${additions[@]}"
            echo
            tail -n +$((tech_section_end + 1)) "$target_file"
        } > "$temp_file"
    else
        cp "$target_file" "$temp_file"
    fi
}

update_recent_changes() {
    local temp_file="$1"
    local temp_file2="$2"
    local changes_section_start
    changes_section_start=$(grep -n "## Recent Changes" "$temp_file" | cut -d: -f1)

    if [[ -z "$changes_section_start" ]]; then cp "$temp_file" "$temp_file2"; return 0; fi

    local changes_section_end
    changes_section_end=$(tail -n +$((changes_section_start + 1)) "$temp_file" | grep -n "^## \|^$" | head -1 | cut -d: -f1)
    if [[ -n "$changes_section_end" ]]; then changes_section_end=$((changes_section_start + changes_section_end)); else changes_section_end=$(wc -l < "$temp_file"); fi

    local existing_changes=()
    while IFS= read -r line; do
        if [[ -n "$line" ]] && [[ "$line" == "- "* ]]; then existing_changes+=("$line"); fi
    done < <(sed -n "$((changes_section_start + 1)),$((changes_section_end - 1))p" "$temp_file")

    existing_changes=("${existing_changes[@]:0:2}")

    {
        head -n "$changes_section_start" "$temp_file"
        echo "- $CURRENT_BRANCH: Added $NEW_LANG + $NEW_FRAMEWORK"
        printf '%s\n' "${existing_changes[@]}"
        echo
        tail -n +$((changes_section_end + 1)) "$temp_file"
    } > "$temp_file2"
}

update_last_updated() {
    local temp_file="$1"
    local current_date="$2"
    sed -i.bak "s/Last updated: [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]/Last updated: $current_date/" "$temp_file"
    rm -f "$temp_file.bak"
}

preserve_manual_additions() {
    local target_file="$1"
    local temp_file="$2"
    local manual_start manual_end
    manual_start=$(grep -n "<!-- MANUAL ADDITIONS START -->" "$target_file" 2>/dev/null | cut -d: -f1 || echo "")
    manual_end=$(grep -n "<!-- MANUAL ADDITIONS END -->" "$target_file" 2>/dev/null | cut -d: -f1 || echo "")

    if [[ -n "$manual_start" ]] && [[ -n "$manual_end" ]]; then
        local manual_file="/tmp/manual_additions_$$"
        sed -n "${manual_start},${manual_end}p" "$target_file" > "$manual_file"
        sed -i.bak '/<!-- MANUAL ADDITIONS START -->/,/<!-- MANUAL ADDITIONS END -->/d' "$temp_file"
        rm -f "$temp_file.bak"
        cat "$manual_file" >> "$temp_file"
        rm -f "$manual_file"
    fi
}

update_agent_file() {
    local target_file="$1"
    local agent_name="$2"

    logger_info "Updating $agent_name context file: $target_file"
    local project_name
    project_name=$(basename "$REPO_ROOT")
    local current_date
    current_date=$(date +%Y-%m-%d)

    local target_dir
    target_dir=$(dirname "$target_file")
    mkdir -p "$target_dir"

    if [[ ! -f "$target_file" ]]; then
        local temp_file
        temp_file=$(mktemp) || return 1
        if create_new_agent_file "$target_file" "$temp_file" "$project_name" "$current_date"; then
            mv "$temp_file" "$target_file"
            logger_success "Created new $agent_name context file"
        else
            logger_error "Failed to create new agent file"
            rm -f "$temp_file"
            return 1
        fi
    else
        if [[ ! -r "$target_file" ]] || [[ ! -w "$target_file" ]]; then logger_error "Cannot access file: $target_file"; return 1; fi

        # Check file size
        local file_size
        if [[ "$OSTYPE" == "darwin"* ]]; then
            file_size=$(stat -f%z "$target_file")
        else
            file_size=$(stat -c%s "$target_file")
        fi

        if [[ "$file_size" -gt "$MAX_FILE_SIZE" ]]; then
            logger_warn "File $target_file is too large ($file_size bytes). Skipping."
            return 0
        fi

        local temp_file1="/tmp/agent_update_1_$$"
        local temp_file2="/tmp/agent_update_2_$$"
        update_active_technologies "$target_file" "$temp_file1"
        update_recent_changes "$temp_file1" "$temp_file2"
        update_last_updated "$temp_file2" "$current_date"
        preserve_manual_additions "$target_file" "$temp_file2"
        mv "$temp_file2" "$target_file"
        rm -f "$temp_file1"
        logger_success "Updated existing $agent_name context file"
    fi
}

main() {
    local agent_type="${1:-}"

    get_feature_paths_env
    check_feature_branch "$CURRENT_BRANCH" || return 1

    local new_plan="$FEATURE_DIR/$PLAN_FILE_NAME"
    if ! parse_plan_data "$new_plan"; then return 1; fi

    local success=true

    # Map agent types to files using config variables
    declare -A agent_map
    agent_map["claude"]="$REPO_ROOT/$CLAUDE_FILE_PATH"
    agent_map["gemini"]="$REPO_ROOT/$GEMINI_FILE_PATH"
    agent_map["copilot"]="$REPO_ROOT/$COPILOT_FILE_PATH"
    agent_map["cursor"]="$REPO_ROOT/$CURSOR_FILE_PATH"
    agent_map["qwen"]="$REPO_ROOT/$QWEN_FILE_PATH"
    agent_map["opencode"]="$REPO_ROOT/$AGENTS_FILE_PATH"
    agent_map["codex"]="$REPO_ROOT/$AGENTS_FILE_PATH"
    agent_map["windsurf"]="$REPO_ROOT/$WINDSURF_FILE_PATH"

    declare -A agent_names
    agent_names["claude"]="Claude Code"
    agent_names["gemini"]="Gemini CLI"
    agent_names["copilot"]="GitHub Copilot"
    agent_names["cursor"]="Cursor IDE"
    agent_names["qwen"]="Qwen Code"
    agent_names["opencode"]="opencode"
    agent_names["codex"]="Codex CLI"
    agent_names["windsurf"]="Windsurf"

    if [[ -n "$agent_type" ]]; then
        if [[ -n "${agent_map[$agent_type]}" ]]; then
            update_agent_file "${agent_map[$agent_type]}" "${agent_names[$agent_type]}" || success=false
        else
            logger_error "Unknown agent type '$agent_type'"
            return 1
        fi
    else
        local found_agent=false
        for type in "${!agent_map[@]}"; do
            if [[ -f "${agent_map[$type]}" ]]; then
                update_agent_file "${agent_map[$type]}" "${agent_names[$type]}" || success=false
                found_agent=true
            fi
        done
        if [[ "$found_agent" == false ]]; then
            logger_info "No existing agent files found, creating default Claude file..."
            update_agent_file "${agent_map[claude]}" "${agent_names[claude]}" || success=false
        fi
    fi

    logger_info "Summary of changes:"
    if [[ -n "$NEW_LANG" ]]; then echo "  - Added language: $NEW_LANG"; fi
    if [[ -n "$NEW_FRAMEWORK" ]]; then echo "  - Added framework: $NEW_FRAMEWORK"; fi
    if [[ -n "$NEW_DB" ]] && [[ "$NEW_DB" != "N/A" ]]; then echo "  - Added database: $NEW_DB"; fi

    if [[ "$success" == true ]]; then logger_success "Agent context update completed successfully"; else return 1; fi
}

invoke_speckit_block "Update-Agent-Context" main "$@"
