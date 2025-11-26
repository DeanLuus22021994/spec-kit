#!/usr/bin/env bash
# DevContainer Build Management Script
# Usage: ./docker/devcontainer/build.sh [command] [options]

set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
readonly BAKE_FILE="$PROJECT_ROOT/docker/docker-bake.hcl"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[1;33m'
readonly RESET='\033[0m'

# Logging functions
log_info() { echo -e "${BLUE}INFO${RESET} $*"; }
log_success() { echo -e "${GREEN}SUCCESS${RESET} $*"; }
log_error() { echo -e "${RED}ERROR${RESET} $*"; }
log_warn() { echo -e "${YELLOW}WARN${RESET} $*"; }

# Show usage information
show_usage() {
    cat << 'EOF'
DevContainer Build Management

USAGE:
    docker/devcontainer/build.sh [COMMAND] [OPTIONS]

COMMANDS:
    build           Build all containers (default)
    build-base      Build only the base container
    build-tools     Build base + tools containers
    build-dev       Build full development container
    cache-prewarm   Pre-warm build cache
    clean           Clean build cache and containers
    push            Push containers to registry
    pull            Pull containers from registry
    local           Build local development image
    help            Show this help message

OPTIONS:
    --registry <reg>     Container registry (default: ghcr.io/spec-kit)
    --version <ver>      Version tag (default: latest)
    --platform <plat>    Target platform (default: linux/amd64,linux/arm64)
    --concurrency <num>  Number of concurrent builds (default: 4)
    --no-cache           Disable build cache
    --push               Push after successful build
    --verbose            Enable verbose output

EXAMPLES:
    # Build all containers for local development
    docker/devcontainer/build.sh local

    # Build and push to registry
    docker/devcontainer/build.sh build --push

    # Build for specific platform
    docker/devcontainer/build.sh build --platform linux/arm64

    # Clean and rebuild everything
    docker/devcontainer/build.sh clean && docker/devcontainer/build.sh build

PERFORMANCE TIPS:
    - Use 'cache-prewarm' before building for faster subsequent builds
    - Set DOCKER_BUILDKIT=1 and BUILDKIT_PROGRESS=plain for optimal performance
    - Use local storage drivers for development builds
    - Enable GitHub Actions cache for CI/CD builds

EOF
}

# Parse command line arguments
parse_args() {
    COMMAND="${1:-build}"
    REGISTRY="${REGISTRY:-ghcr.io/spec-kit}"
    VERSION="${VERSION:-latest}"
    PLATFORM="${PLATFORM:-linux/amd64,linux/arm64}"
    CONCURRENT_BUILDS="${CONCURRENT_BUILDS:-4}"
    NO_CACHE=""
    PUSH_AFTER=""
    VERBOSE=""

    shift || true

    while [[ $# -gt 0 ]]; do
        case $1 in
            --registry)
                REGISTRY="$2"; shift 2 ;;
            --version)
                VERSION="$2"; shift 2 ;;
            --platform)
                PLATFORM="$2"; shift 2 ;;
            --concurrency|--concurrent-builds)
                CONCURRENT_BUILDS="$2"; shift 2 ;;
            --no-cache)
                NO_CACHE="--no-cache"; shift ;;
            --push)
                PUSH_AFTER="--push"; shift ;;
            --verbose)
                VERBOSE="--progress=plain"; shift ;;
            *)
                log_error "Unknown option: $1"; exit 1 ;;
        esac
    done
}

# Check prerequisites
check_prereqs() {
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker is required but not installed"
        exit 1
    fi

    if ! docker buildx version >/dev/null 2>&1; then
        log_error "Docker Buildx is required but not available"
        exit 1
    fi

    if [ ! -f "$BAKE_FILE" ]; then
        log_error "Docker Bake file not found: $BAKE_FILE"
        exit 1
    fi
}

# Build containers using Docker Bake
build_containers() {
    local target="$1"
    local extra_args=("${@:2}")

    log_info "Building $target containers..."
    log_info "Registry: $REGISTRY"
    log_info "Version: $VERSION"
    log_info "Platform: $PLATFORM"

    # Set environment variables for Docker Bake
    export REGISTRY="$REGISTRY"
    export VERSION="$VERSION"
    export BUILDKIT_PROGRESS="${VERBOSE:-auto}"
    export DOCKER_BUILDKIT=1

    # Build command
    local cmd=(
        docker buildx bake
        --file "$BAKE_FILE"
        --set "*.platform=$PLATFORM"
        $NO_CACHE
        $PUSH_AFTER
        $VERBOSE
        "${extra_args[@]}"
        "$target"
    )

    log_info "Running: ${cmd[*]}"

    # Allow local filesystem read without prompts
    export BUILDX_BAKE_ENTITLEMENTS_FS=0

    if "${cmd[@]}"; then
        log_success "$target build completed successfully"
    else
        log_error "$target build failed"
        exit 1
    fi
}

# Clean build artifacts
clean_build() {
    log_info "Cleaning build cache and containers..."

    # Remove build cache
    docker builder prune -f || true

    # Remove dev containers
    docker images -q "ghcr.io/spec-kit/devcontainer" | head -10 | xargs -r docker rmi -f || true
    docker images -q "spec-kit-devcontainer" | head -10 | xargs -r docker rmi -f || true

    log_success "Build cleanup completed"
}

# Added cache performance functions
cache_stats() {
  log_info "Cache statistics:"
  docker buildx du -v | grep -E 'cache|regular|total'

  # Show hit ratio if available
  if command -v jq >/dev/null 2>&1 && [ -f "$BUILD_STATS_FILE" ]; then
    HITS=$(jq '.hits // 0' "$BUILD_STATS_FILE")
    MISSES=$(jq '.misses // 0' "$BUILD_STATS_FILE")
    TOTAL=$((HITS + MISSES))

    if [ "$TOTAL" -gt 0 ]; then
      RATIO=$((HITS * 100 / TOTAL))
      log_success "Cache hit ratio: $RATIO% ($HITS hits, $MISSES misses)"
    fi
  fi
}

# Enhanced prewarm function for better subsequent builds
prewarm_cache() {
  log_info "Pre-warming build cache with parallel processing..."
  export REGISTRY="$REGISTRY"
  export VERSION="$VERSION"

  mkdir -p "${PROJECT_ROOT}/.devcontainer/.build-cache"
  BUILD_STATS_FILE="${PROJECT_ROOT}/.devcontainer/.build-cache/stats.json"

  BUILDKIT_PROGRESS=plain docker buildx bake \
    --file "$BAKE_FILE" \
    --set "*.platform=$PLATFORM" \
    --set "*.args.BUILDKIT_INLINE_CACHE=1" \
    --set "*.args.CONCURRENT_BUILDS=$CONCURRENT_BUILDS" \
    cache-prewarm | tee /tmp/build-log

  CACHE_HITS=$(grep -c "CACHED" /tmp/build-log || echo 0)
  CACHE_MISSES=$(grep -c "DONE" /tmp/build-log | awk '{print $1-"'$CACHE_HITS'"}' || echo 0)
  echo "{\"hits\":$CACHE_HITS,\"misses\":$CACHE_MISSES}" > "$BUILD_STATS_FILE"

  log_success "Cache pre-warming completed with $CACHE_HITS cache hits"
  rm -f /tmp/build-log
}

# Main execution
main() {
    parse_args "$@"
    check_prereqs

    cd "$PROJECT_ROOT"

    case "$COMMAND" in
        build)
            build_containers "all"
            ;;
        build-base)
            build_containers "base"
            ;;
        build-tools)
            build_containers "tools"
            ;;
        build-dev)
            build_containers "development"
            ;;
        cache-prewarm)
            prewarm_cache
            ;;
        clean)
            clean_build
            ;;
        local)
            build_containers "local"
            ;;
        push)
            # Push existing images
            docker push "$REGISTRY/devcontainer:base-$VERSION" || true
            docker push "$REGISTRY/devcontainer:tools-$VERSION" || true
            docker push "$REGISTRY/devcontainer:dev-$VERSION" || true
            docker push "$REGISTRY/devcontainer:latest" || true
            log_success "Container push completed"
            ;;
        pull)
            # Pull images
            docker pull "$REGISTRY/devcontainer:latest" || true
            docker pull "$REGISTRY/devcontainer:dev-$VERSION" || true
            log_success "Container pull completed"
            ;;
        help)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            echo
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
