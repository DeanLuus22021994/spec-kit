#!/usr/bin/env bash
# YAML Validation Script - Kantra CLI Integration
# Runs Red Hat MTA YAML validation rules against repository
# Location: tools/.config/scripts/validate-yaml.sh

set -euo pipefail

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Paths
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detect if running in container (script in /usr/local/bin)
if [[ "${SCRIPT_DIR}" == "/usr/local/bin" ]]; then
    readonly WORKSPACE_ROOT="/workspace"
    readonly RULES_DIR="${WORKSPACE_ROOT}/.config/validation/rules"
    readonly REPORTS_DIR="${WORKSPACE_ROOT}/.config/validation/reports/latest"
    readonly PROFILES_DIR="${WORKSPACE_ROOT}/.config/validation/profiles"
    readonly INPUT_DIR="${WORKSPACE_ROOT}"
else
    readonly WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
    readonly RULES_DIR="${WORKSPACE_ROOT}/tools/.config/validation/rules"
    readonly REPORTS_DIR="${WORKSPACE_ROOT}/tools/.config/validation/reports/latest"
    readonly PROFILES_DIR="${WORKSPACE_ROOT}/tools/.config/validation/profiles"
    readonly INPUT_DIR="${WORKSPACE_ROOT}"
fi

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

check_kantra() {
    if ! command -v kantra >/dev/null 2>&1; then
        log_error "Kantra CLI not found. Install from: https://github.com/konveyor/kantra"
        log_info "Or use containerized version via 'make validate-yaml'"
        return 1
    fi

    local version
    version=$(kantra --version 2>&1 || echo "unknown")
    log_info "Kantra version: ${version}"
}

load_profile() {
    local profile_file="${PROFILES_DIR}/${PROFILE}.yaml"

    if [ ! -f "${profile_file}" ]; then
        log_error "Profile not found: ${profile_file}"
        log_info "Available profiles: strict, recommended, minimal, ci-cd, development"
        return 1
    fi

    log_info "Using profile: ${PROFILE}"

    # Profile determines label selector if not explicitly set
    if [ -z "${LABEL_SELECTOR}" ]; then
        case "${PROFILE}" in
            strict)
                LABEL_SELECTOR=""
                log_info "Profile mode: All rules (zero tolerance)"
                ;;
            recommended)
                LABEL_SELECTOR=""
                log_info "Profile mode: Mandatory and optional rules"
                ;;
            minimal)
                LABEL_SELECTOR="category=mandatory"
                log_info "Profile mode: Mandatory rules only"
                ;;
            ci-cd)
                LABEL_SELECTOR="category=mandatory"
                log_info "Profile mode: CI/CD optimized (mandatory only)"
                ;;
            development)
                LABEL_SELECTOR=""
                log_info "Profile mode: Developer-friendly (all warnings)"
                ;;
        esac
    fi
}

prepare_reports_dir() {
    log_info "Preparing reports directory: ${REPORTS_DIR}"
    mkdir -p "${REPORTS_DIR}"

    # Clean previous reports (optional)
    if [ -d "${REPORTS_DIR}/static-report" ]; then
        log_warning "Removing previous report..."
        rm -rf "${REPORTS_DIR}/static-report"
    fi
}

run_validation() {
    local run_local_flag
    if [ "${RUN_MODE}" = "local" ]; then
        run_local_flag="--run-local"
    else
        run_local_flag="--run-local=false"
    fi

    log_info "Starting YAML validation..."
    log_info "  Input: ${INPUT_DIR}"
    log_info "  Rules: ${RULES_DIR}"
    log_info "  Output: ${REPORTS_DIR}"
    log_info "  Mode: ${RUN_MODE}"

    if [ -n "${LABEL_SELECTOR}" ]; then
        log_info "  Label selector: ${LABEL_SELECTOR}"
    fi

    local cmd=(
        kantra analyze
        --input "${INPUT_DIR}"
        --output "${REPORTS_DIR}"
        --rules "${RULES_DIR}"
        --enable-default-rulesets=false
        --overwrite
        --mode=source-only
        "${run_local_flag}"
    )

    if [ -n "${LABEL_SELECTOR}" ]; then
        cmd+=(--label-selector="${LABEL_SELECTOR}")
    fi

    # Run analysis
    if "${cmd[@]}"; then
        log_success "YAML validation completed successfully"
        return 0
    else
        local exit_code=$?
        log_error "YAML validation failed with exit code: ${exit_code}"
        return "${exit_code}"
    fi
}

show_report_location() {
    if [ -f "${REPORTS_DIR}/static-report/index.html" ]; then
        log_success "Static report generated:"
        log_info "  file://${REPORTS_DIR}/static-report/index.html"
    fi

    if [ -f "${REPORTS_DIR}/output.yaml" ]; then
        log_info "Machine-readable output:"
        log_info "  ${REPORTS_DIR}/output.yaml"
    fi
}

show_summary() {
    if [ -f "${REPORTS_DIR}/output.yaml" ]; then
        log_info "Parsing validation results..."

        # Count incidents by category (requires yq or grep)
        if command -v yq >/dev/null 2>&1; then
            local total_incidents
            total_incidents=$(yq eval '.incidents | length' "${REPORTS_DIR}/output.yaml" 2>/dev/null || echo "0")

            if [ "${total_incidents}" -gt 0 ]; then
                log_warning "Found ${total_incidents} YAML issues"
            else
                log_success "No YAML issues found!"
            fi
        fi
    fi
}

main() {
    log_info "=== YAML Validation with Kantra CLI ==="

    # Check prerequisites
    check_kantra || return 1

    # Load profile configuration
    load_profile || return 1

    # Verify rules directory exists
    if [ ! -d "${RULES_DIR}" ]; then
        log_error "Rules directory not found: ${RULES_DIR}"
        return 1
    fi

    if [ ! -f "${RULES_DIR}/ruleset.yaml" ]; then
        log_error "Ruleset file not found: ${RULES_DIR}/ruleset.yaml"
        return 1
    fi

    # Prepare environment
    prepare_reports_dir

    # Run validation
    if run_validation; then
        show_report_location
        show_summary
        log_success "=== Validation Complete ==="
        return 0
    else
        local exit_code=$?
        show_report_location
        log_error "=== Validation Failed ==="
        return "${exit_code}"
    fi
}

# Handle script arguments
while [[ $# -gt 0 ]]; do
    case "${1}" in
        --profile)
            PROFILE="${2}"
            shift 2
            ;;
        --mandatory)
            LABEL_SELECTOR="category=mandatory"
            shift
            ;;
        --optional)
            LABEL_SELECTOR="category=optional"
            shift
            ;;
        --potential)
            LABEL_SELECTOR="category=potential"
            shift
            ;;
        --help|-h)
            cat <<EOF
Usage: $0 [OPTIONS]

Run YAML validation using Kantra CLI and MTA rules.

OPTIONS:
  --profile NAME  Use validation profile (strict, recommended, minimal, ci-cd, development)
  --mandatory     Run only mandatory rules
  --optional      Run only optional rules
  --potential     Run only potential rules
  --help, -h      Show this help message

ENVIRONMENT VARIABLES:
  PROFILE         Validation profile name (default: recommended)
  LABEL_SELECTOR  Custom label selector expression
  RUN_MODE        Analysis mode: local (default) or hybrid

PROFILES:
  strict          Zero-tolerance, all rules enforced
  recommended     Balanced profile (default)
  minimal         Mandatory rules only
  ci-cd           CI/CD optimized
  development     Developer-friendly with all warnings

EXAMPLES:
  # Run with recommended profile (default)
  $0

  # Run with strict profile
  $0 --profile strict

  # Run mandatory rules only
  $0 --mandatory

  # Custom label selector
  LABEL_SELECTOR="category=mandatory" $0

  # Use hybrid mode with strict profile
  RUN_MODE=hybrid $0 --profile strict

EOF
            exit 0
            ;;
        *)
            log_error "Unknown option: ${1}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Execute main function
main
