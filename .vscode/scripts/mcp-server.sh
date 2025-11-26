#!/bin/bash
# MCP Development Server Manager
# Manages Docker-based and local MCP servers for development

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker/mcp/compose.mcp.yml"
MCP_CONFIG_FILE="$SCRIPT_DIR/mcp.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Check if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_warning "Docker not found. MCP servers will run locally."
        return 1
    fi

    if ! docker info &> /dev/null; then
        log_warning "Docker daemon not running. MCP servers will run locally."
        return 1
    fi

    return 0
}

# Check if required tools are available
check_requirements() {
    local missing_tools=()

    if ! command -v node &> /dev/null; then
        missing_tools+=("node")
    fi

    if ! command -v npx &> /dev/null; then
        missing_tools+=("npx")
    fi

    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install Node.js (which includes npx)"
        return 1
    fi

    return 0
}

# Start MCP servers using Docker Compose
start_docker_servers() {
    local profile="${1:-development}"

    log_info "Starting MCP servers using Docker (profile: $profile)..."

    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        log_error "Docker Compose file not found: $DOCKER_COMPOSE_FILE"
        return 1
    fi

    # Export environment variables
    export GITHUB_TOKEN="${GITHUB_TOKEN:-}"
    export DISPLAY="${DISPLAY:-:0}"

    cd "$PROJECT_ROOT"
    docker-compose -f "$DOCKER_COMPOSE_FILE" --profile "$profile" up -d

    log_success "MCP servers started with profile: $profile"
    log_info "Use 'docker-compose -f $DOCKER_COMPOSE_FILE logs -f' to view logs"
}

# Stop MCP servers
stop_docker_servers() {
    log_info "Stopping MCP servers..."

    cd "$PROJECT_ROOT"
    docker-compose -f "$DOCKER_COMPOSE_FILE" down

    log_success "MCP servers stopped"
}

# Install MCP server packages locally
install_local_servers() {
    log_info "Installing MCP servers locally..."

    local servers=(
        "@modelcontextprotocol/server-github"
        "@modelcontextprotocol/server-playwright"
        "@modelcontextprotocol/server-filesystem"
    )

    for server in "${servers[@]}"; do
        log_info "Installing $server..."
        npm install -g "$server" || log_warning "Failed to install $server"
    done

    log_success "Local MCP server installation completed"
}

# Check status of MCP servers
status() {
    log_info "Checking MCP server status..."

    if check_docker; then
        cd "$PROJECT_ROOT"
        docker-compose -f "$DOCKER_COMPOSE_FILE" ps
    else
        log_info "Docker not available - checking local installations..."

        local servers=(
            "@modelcontextprotocol/server-github"
            "@modelcontextprotocol/server-playwright"
            "@modelcontextprotocol/server-filesystem"
            "@modelcontextprotocol/server-git"
            "@modelcontextprotocol/server-python"
            "@modelcontextprotocol/server-docker"
        )

        for server in "${servers[@]}"; do
            if npm list -g "$server" &> /dev/null; then
                log_success "$server: installed"
            else
                log_warning "$server: not installed"
            fi
        done
    fi
}

# Show logs from Docker containers
logs() {
    local service="${1:-}"

    cd "$PROJECT_ROOT"
    if [ -n "$service" ]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f "$service"
    else
        docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f
    fi
}

# Restart specific service
restart_service() {
    local service="${1:-}"

    if [ -z "$service" ]; then
        log_error "Service name required"
        return 1
    fi

    log_info "Restarting service: $service"

    cd "$PROJECT_ROOT"
    docker-compose -f "$DOCKER_COMPOSE_FILE" restart "$service"

    log_success "Service $service restarted"
}

# Show help
show_help() {
    cat << EOF
MCP Development Server Manager

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    start [profile]     Start MCP servers using Docker Compose
                       Profiles: development, testing
                       Default: development

    stop               Stop MCP servers

    restart [service]  Restart a specific service

    status             Check status of MCP servers

    logs [service]     Show logs from Docker containers
                      If no service specified, shows all logs

    install-local      Install MCP servers locally (fallback)

    check              Check system requirements

    help               Show this help message

Examples:
    $0 start                    # Start with development profile
    $0 start testing           # Start with testing profile (includes Playwright)
    $0 logs mcp-playwright     # Show Playwright server logs
    $0 restart mcp-github      # Restart GitHub server
    $0 status                  # Check server status

Environment Variables:
    GITHUB_TOKEN      GitHub Personal Access Token (required for GitHub MCP)
    DISPLAY           X11 display for GUI applications (default: :0)

EOF
}

# Main command dispatcher
main() {
    local command="${1:-help}"

    case "$command" in
        "start")
            if ! check_requirements; then
                exit 1
            fi

            local profile="${2:-development}"

            if check_docker; then
                start_docker_servers "$profile"
            else
                log_warning "Docker not available. Please install MCP servers locally first."
                log_info "Run: $0 install-local"
                exit 1
            fi
            ;;

        "stop")
            stop_docker_servers
            ;;

        "restart")
            restart_service "$2"
            ;;

        "status")
            status
            ;;

        "logs")
            logs "$2"
            ;;

        "install-local")
            if ! check_requirements; then
                exit 1
            fi
            install_local_servers
            ;;

        "check")
            check_requirements
            check_docker
            log_info "System check completed"
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
