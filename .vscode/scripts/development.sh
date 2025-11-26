#!/bin/bash
# Development Utilities for Spec-Kit
# Provides common development tasks and utilities

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${PURPLE}[DEBUG]${NC} $1"
}

# Development environment setup
setup_dev_env() {
    log_info "Setting up development environment..."

    cd "$PROJECT_ROOT"

    # Install Python dependencies
    log_info "Installing Python dependencies..."
    python3 -m pip install --break-system-packages -e .

    # Install development tools
    log_info "Installing development tools..."
    python3 -m pip install --break-system-packages \
        black flake8 mypy pytest pytest-cov

    # Install MCP servers
    if command -v npm &> /dev/null; then
        log_info "Installing MCP servers..."
        npm install -g \
            @modelcontextprotocol/server-github \
            @modelcontextprotocol/server-playwright \
            @modelcontextprotocol/server-filesystem
    else
        log_warning "npm not found - skipping MCP server installation"
    fi

    log_success "Development environment setup complete!"
}

# Code quality checks
quality_check() {
    log_info "Running code quality checks..."

    cd "$PROJECT_ROOT"

    # Format code
    log_info "Formatting code with Black..."
    python3 -m black --line-length 88 src/

    # Lint code
    log_info "Linting code with Flake8..."
    python3 -m flake8 src/ --max-line-length=88 --extend-ignore=E203,W503

    # Type check
    log_info "Type checking with MyPy..."
    python3 -m mypy src/ --ignore-missing-imports

    log_success "Code quality checks complete!"
}

# Run tests
run_tests() {
    log_info "Running tests..."

    cd "$PROJECT_ROOT"

    if [ -d "tests" ]; then
        python3 -m pytest tests/ -v --cov=src/
    else
        log_info "Running CLI tests..."
        python3 src/specify_cli/__init__.py --help > /dev/null
        python3 src/specify_cli/__init__.py check > /dev/null
        log_success "CLI tests passed!"
    fi
}

# Build package
build_package() {
    log_info "Building package..."

    cd "$PROJECT_ROOT"

    # Clean previous builds
    rm -rf build/ dist/ *.egg-info/

    # Build package
    python3 -m build

    log_success "Package built successfully!"
}

# Clean project
clean_project() {
    log_info "Cleaning project..."

    cd "$PROJECT_ROOT"

    # Remove build artifacts
    rm -rf build/ dist/ *.egg-info/

    # Remove Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true

    # Remove test artifacts
    rm -rf .pytest_cache/ .coverage htmlcov/

    # Remove MyPy cache
    rm -rf .mypy_cache/

    log_success "Project cleaned!"
}

# Development server
dev_server() {
    log_info "Starting development server..."

    # Start MCP servers
    "$SCRIPT_DIR/mcp-server.sh" start development &

    # Start file watcher (if available)
    if command -v watchdog &> /dev/null; then
        watchdog src/ --auto-restart python3 src/specify_cli/__init__.py &
    fi

    log_success "Development server started!"
    log_info "Press Ctrl+C to stop"

    wait
}

# Environment info
env_info() {
    log_info "Development Environment Information"
    echo

    # Python info
    echo -e "${CYAN}Python Environment:${NC}"
    python3 --version
    echo "Python Path: $(which python3)"
    echo "PYTHONPATH: ${PYTHONPATH:-Not set}"
    echo

    # Node.js info
    if command -v node &> /dev/null; then
        echo -e "${CYAN}Node.js Environment:${NC}"
        node --version
        npm --version
        echo "Node Path: $(which node)"
        echo
    fi

    # Git info
    if command -v git &> /dev/null; then
        echo -e "${CYAN}Git Information:${NC}"
        git --version
        git config --get user.name || echo "Name: Not configured"
        git config --get user.email || echo "Email: Not configured"
        echo
    fi

    # Docker info
    if command -v docker &> /dev/null; then
        echo -e "${CYAN}Docker Information:${NC}"
        docker --version
        docker info --format "Server Version: {{.ServerVersion}}" 2>/dev/null || echo "Docker daemon not running"
        echo
    fi

    # VS Code info
    if command -v code &> /dev/null; then
        echo -e "${CYAN}VS Code Information:${NC}"
        code --version | head -1
        echo
    fi
}

# Show help
show_help() {
    cat << EOF
Development Utilities for Spec-Kit

Usage: $0 [COMMAND]

Commands:
    setup           Setup development environment
    quality         Run code quality checks (format, lint, type-check)
    test            Run tests
    build           Build package
    clean           Clean project artifacts
    server          Start development server
    info            Show environment information
    help            Show this help message

Examples:
    $0 setup        # Setup development environment
    $0 quality      # Run all quality checks
    $0 test         # Run tests
    $0 build        # Build package
    $0 clean        # Clean artifacts
    $0 server       # Start dev server
    $0 info         # Show environment info

Environment Variables:
    DEBUG           Enable debug output (set to 1)
    PYTHONPATH      Python module search path
    GITHUB_TOKEN    GitHub token for MCP server

EOF
}

# Main command dispatcher
main() {
    local command="${1:-help}"

    # Enable debug mode if DEBUG is set
    if [[ "${DEBUG:-}" == "1" ]]; then
        set -x
    fi

    case "$command" in
        "setup")
            setup_dev_env
            ;;

        "quality")
            quality_check
            ;;

        "test")
            run_tests
            ;;

        "build")
            build_package
            ;;

        "clean")
            clean_project
            ;;

        "server")
            dev_server
            ;;

        "info")
            env_info
            ;;

        "help"|"-h"|"--help")
            show_help
            ;;

        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
