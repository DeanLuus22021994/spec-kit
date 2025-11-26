#!/usr/bin/env bash
set -e

# Parse arguments
JSON_MODE=false
for arg in "$@"; do
  case "$arg" in
    --json)
      JSON_MODE=true
      ;;
    --help|-h)
      echo "Usage: $0 [--json]"
      exit 0
      ;;
  esac
done

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get paths
eval $(get_feature_paths)

# Check prerequisites
check_feature_branch "$CURRENT_BRANCH" || exit 1

# Output results
if $JSON_MODE; then
  printf '{"FEATURE_SPEC":"%s","IMPL_PLAN":"%s","TASKS_FILE":"%s","SPECS_DIR":"%s","BRANCH":"%s"}\n' \
    "$FEATURE_SPEC" "$IMPL_PLAN" "$TASKS_FILE" "$FEATURE_DIR" "$CURRENT_BRANCH"
else
  echo "FEATURE_SPEC: $FEATURE_SPEC"
  echo "IMPL_PLAN: $IMPL_PLAN"
  echo "TASKS_FILE: $TASKS_FILE"
  echo "SPECS_DIR: $FEATURE_DIR"
  echo "BRANCH: $CURRENT_BRANCH"
fi
