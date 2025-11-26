#!/usr/bin/env bash

# Plan Parsing Utilities

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
