#!/usr/bin/env bash
# shellcheck source=scripts/bash/lib/speckit.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/speckit.sh"

main() {
    local json_mode=false
    local args=()
    for arg in "$@"; do
        case "$arg" in
            --json) json_mode=true ;;
            --help|-h) echo "Usage: $0 [--json] <feature_description>"; exit 0 ;;
            *) args+=("$arg") ;;
        esac
    done

    local feature_description="${args[*]}"
    if [ -z "$feature_description" ]; then
        logger_error "Usage: $0 [--json] <feature_description>"
        return 1
    fi

    local repo_root
    repo_root=$(get_repo_root)
    local specs_dir="$repo_root/$SPECS_DIR_NAME"
    mkdir -p "$specs_dir"

    local highest=0
    if [ -d "$specs_dir" ]; then
        for dir in "$specs_dir"/*; do
            [ -d "$dir" ] || continue
            local dirname
            dirname=$(basename "$dir")
            local number
            number=$(echo "$dirname" | grep -o '^[0-9]\+' || echo "0")
            number=$((10#$number))
            if [ "$number" -gt "$highest" ]; then highest=$number; fi
        done
    fi

    local next=$((highest + 1))
    local feature_num
    feature_num=$(printf "%03d" "$next")

    local branch_name
    branch_name=$(echo "$feature_description" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//')
    local words
    words=$(echo "$branch_name" | tr '-' '\n' | grep -v '^$' | head -3 | tr '\n' '-' | sed 's/-$//')
    branch_name="${feature_num}-${words}"

    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        git checkout -b "$branch_name" >/dev/null 2>&1
        logger_success "Created branch: $branch_name"
    else
        logger_warn "Git repository not detected; skipped branch creation for $branch_name"
    fi

    local feature_dir="$specs_dir/$branch_name"
    mkdir -p "$feature_dir"

    local template="$repo_root/$TEMPLATES_DIR_NAME/$SPEC_TEMPLATE_NAME"
    local spec_file="$feature_dir/spec.md"
    if [ -f "$template" ]; then
        cp "$template" "$spec_file"
    else
        touch "$spec_file"
    fi
    logger_success "Created spec file: $spec_file"

    if $json_mode; then
        printf '{"BRANCH_NAME":"%s","SPEC_FILE":"%s","FEATURE_NUM":"%s"}\n' "$branch_name" "$spec_file" "$feature_num"
    else
        logger_info "BRANCH_NAME: $branch_name"
        logger_info "SPEC_FILE: $spec_file"
        logger_info "FEATURE_NUM: $feature_num"
    fi
}

invoke_speckit_block "Create-New-Feature" main "$@"
