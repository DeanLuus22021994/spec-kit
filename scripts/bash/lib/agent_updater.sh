#!/usr/bin/env bash

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
