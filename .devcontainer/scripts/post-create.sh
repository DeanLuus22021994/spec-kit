#!/usr/bin/env bash
# DevContainer Post-Create Script - Clean Implementation
set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
readonly CONFIG_FILE="$PROJECT_ROOT/.devcontainer/config.yaml"
readonly SETUP_MARKER="$PROJECT_ROOT/.devcontainer/.setup-complete"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly RESET='\033[0m'

# Logging functions
log_info() { echo -e "${BLUE}INFO${RESET} $*"; }
log_success() { echo -e "${GREEN}PASS${RESET} $*"; }
log_error() { echo -e "${RED}FAIL${RESET} $*"; }

# Check if setup needs to be run
should_run_setup() {
    if [ ! -f "$SETUP_MARKER" ]; then
        return 0  # No marker, run setup
    fi

    if [ ! -f "$CONFIG_FILE" ]; then
        return 0  # No config, run setup
    fi

    # Compare timestamps if available
    if command -v stat >/dev/null 2>&1; then
        local config_modified setup_completed
        config_modified=$(stat -c %Y "$CONFIG_FILE" 2>/dev/null || echo 0)
        setup_completed=$(stat -c %Y "$SETUP_MARKER" 2>/dev/null || echo 0)

        if [ "$config_modified" -gt "$setup_completed" ]; then
            return 0  # Config newer than setup, run setup
        fi
    fi

    return 1  # Skip setup
}

# Execute setup commands with error handling
run_setup() {
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python3 required for YAML parsing"
        return 1
    fi

    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "Config file not found: $CONFIG_FILE"
        return 1
    fi

    export CONFIG_FILE SETUP_MARKER
    python3 << 'EOF'
import yaml
import subprocess
import sys
import os
import time

config_file = os.environ.get('CONFIG_FILE')
setup_marker = os.environ.get('SETUP_MARKER')

try:
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    setup_commands = config.get('setup', {}).get('commands', [])
    completed = 0
    failed = 0
    failed_commands = []

    for setup in setup_commands:
        name = setup.get('name', 'unnamed')
        description = setup.get('description', name)
        command = setup.get('command', '')

        print(f"Running: {description}")
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"\033[0;32m✓\033[0m {description}")
                completed += 1
            else:
                print(f"\033[0;31m✗\033[0m {description}")
                if result.stderr.strip():
                    print(f"  Error: {result.stderr.strip()}")
                failed += 1
                failed_commands.append(name)
        except Exception as e:
            print(f"\033[0;31m✗\033[0m {name}: {str(e)}")
            failed += 1
            failed_commands.append(name)

    # Summary
    total = completed + failed
    if total > 0:
        print(f"\nSetup Summary: {completed}/{total} commands completed")
        if failed_commands:
            print(f"Failed: {', '.join(failed_commands)}")

    # Create success marker if most commands succeeded
    if failed == 0 or (completed > failed):
        if setup_marker:
            os.makedirs(os.path.dirname(setup_marker), exist_ok=True)
            with open(setup_marker, 'w') as f:
                f.write(f"Setup completed: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Commands: {completed} completed, {failed} failed\n")
                f.write(f"Config file: {config_file}\n")

    sys.exit(0 if failed == 0 else 1)

except Exception as e:
    print(f"\033[0;31mERROR\033[0m Failed to parse configuration: {str(e)}")
    sys.exit(1)
EOF
}

# Main execution
main() {
    echo "DevContainer Post-Create Setup"
    echo "------------------------------"

    if should_run_setup; then
        log_info "Running setup commands..."

        if run_setup; then
            echo
            log_success "Setup completed successfully"

            # Set script permissions
            find "$PROJECT_ROOT/.devcontainer/scripts" -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true

            exit 0
        else
            echo
            log_error "Setup completed with failures"
            exit 1
        fi
    else
        echo "✓ Setup already completed - skipping"
        exit 0
    fi
}

main "$@"
