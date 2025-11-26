#!/usr/bin/env bash

get_repo_root() {
    git rev-parse --show-toplevel
}

get_current_branch() {
    git rev-parse --abbrev-ref HEAD
}

check_feature_branch() {
    local branch="$1"
    if [[ ! "$branch" =~ ^[0-9]{3}- ]]; then
        logger_error "Not on a feature branch. Current branch: $branch"
        logger_error "Feature branches should be named like: 001-feature-name"
        return 1
    fi
    return 0
}

get_feature_dir() {
    local repo_root="$1"
    local branch="$2"
    echo "$repo_root/specs/$branch"
}

get_feature_paths_env() {
    export REPO_ROOT
    REPO_ROOT=$(get_repo_root)
    export CURRENT_BRANCH
    CURRENT_BRANCH=$(get_current_branch)
    export FEATURE_DIR
    FEATURE_DIR=$(get_feature_dir "$REPO_ROOT" "$CURRENT_BRANCH")
    export FEATURE_SPEC="$FEATURE_DIR/spec.md"
    export IMPL_PLAN="$FEATURE_DIR/plan.md"
    export TASKS="$FEATURE_DIR/tasks.md"
    export RESEARCH="$FEATURE_DIR/research.md"
    export DATA_MODEL="$FEATURE_DIR/data-model.md"
    export QUICKSTART="$FEATURE_DIR/quickstart.md"
    export CONTRACTS_DIR="$FEATURE_DIR/contracts"
}

check_file_exists() {
    local path="$1"
    local description="$2"
    if [[ -f "$path" ]]; then
        logger_success "$description found"
        return 0
    else
        logger_warn "$description not found"
        return 1
    fi
}

check_dir_has_files() {
    local path="$1"
    local description="$2"
    if [[ -d "$path" ]] && [[ -n "$(ls -A "$path" 2>/dev/null)" ]]; then
        logger_success "$description found (with files)"
        return 0
    else
        logger_warn "$description not found or empty"
        return 1
    fi
}
