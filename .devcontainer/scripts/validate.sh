#!/usr/bin/env bash
# DevContainer Validation Script - Clean Implementation
set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
readonly CONFIG_FILE="$PROJECT_ROOT/.devcontainer/config.yaml"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[1;36m'
readonly BOLD='\033[1m'
readonly RESET='\033[0m'

# Logging functions
log_info() { echo -e "${BLUE}INFO${RESET} $*"; }
log_success() { echo -e "${GREEN}PASS${RESET} $*"; }
log_error() { echo -e "${RED}FAIL${RESET} $*"; }

# Validation execution with enhanced categorization
execute_validations() {
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python3 required for YAML parsing"
        return 1
    fi

    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "Config file not found: $CONFIG_FILE"
        return 1
    fi

    export CONFIG_FILE
    python3 << 'EOF'
import yaml
import subprocess
import sys
import os
from collections import defaultdict

config_file = os.environ.get('CONFIG_FILE')

try:
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    validations = config.get('validation', {}).get('commands', [])

    # Enhanced category mapping
    categories = {
        'check_devcontainer_cli': 'Core Infrastructure',
        'check_git_config': 'Core Infrastructure',
        'check_docker_access': 'Core Infrastructure',
        'check_node_npm': 'Core Infrastructure',
        'check_gpu_passthrough': 'GPU Support',
        'check_devcontainer_files': 'Project Structure',
        'check_script_permissions': 'Project Structure',
        'check_post_create_implementation': 'Project Structure',
        'check_yaml_syntax': 'Project Structure',
        'check_github_token': 'Authentication',
        'check_python_interpreter': 'Python Environment',
        'check_ruff_installation': 'Python Environment',
        'check_ruff_configuration': 'Python Environment',
        'check_python_tools': 'Python Environment',
        'check_pytest_installation': 'Python Environment',
        'check_extension_config': 'VS Code Configuration',
        'check_formatting_integration': 'Development Tools',
        'check_linting_integration': 'Development Tools',
        'check_devcontainer_config': 'Integration Validation'
    }

    # Group results by category
    results = defaultdict(list)
    total_passed = 0
    total_failed = 0
    failed_checks = []

    for validation in validations:
        name = validation.get('name', 'unnamed')
        description = validation.get('description', name)
        command = validation.get('command', '')
        error_message = validation.get('error_message', 'Check failed')
        category = categories.get(name, 'Other')

        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                results[category].append(('✓', description, True))
                total_passed += 1
            else:
                results[category].append(('✗', error_message, False))
                total_failed += 1
                failed_checks.append(name.replace('check_', ''))
        except Exception as e:
            results[category].append(('✗', f"{name}: {str(e)}", False))
            total_failed += 1
            failed_checks.append(name.replace('check_', ''))

    # Display results by category
    for category, checks in results.items():
        print(f"\n\033[1;36m{category}:\033[0m")
        for symbol, message, passed in checks:
            color = "\033[0;32m" if passed else "\033[0;31m"
            print(f"  {color}{symbol}\033[0m {message}")

    # Summary
    total = total_passed + total_failed
    print(f"\n\033[1mSummary:\033[0m {total_passed}/{total} checks passed")

    if failed_checks:
        print(f"\033[1;31mFailed:\033[0m {', '.join(failed_checks)}")

    sys.exit(0 if total_failed == 0 else 1)

except Exception as e:
    print(f"\033[0;31mERROR\033[0m Failed to parse configuration: {str(e)}")
    sys.exit(1)
EOF
}

# Main execution
main() {
    echo "Development Environment Status"
    echo "=============================="

    if execute_validations; then
        echo
        log_success "Environment ready for development"
        exit 0
    else
        echo
        log_error "Environment requires attention"
        exit 1
    fi
}

main "$@"
