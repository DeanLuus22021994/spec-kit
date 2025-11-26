# Docker Bake Configuration - High Performance Multi-Stage Builds
# Usage: docker buildx bake --file docker-bake.hcl
variable "REGISTRY" {
  default = "ghcr.io/spec-kit"
}

variable "VERSION" {
  default = "latest"
}

variable "BUILDKIT_PROGRESS" {
  default = "plain"
}

variable "DOCKER_BUILDKIT" {
  default = "1"
}

# ============================================================================
# BASE TARGET - Minimal System Setup
# ============================================================================
target "base" {
  dockerfile = "docker/devcontainer/base.dockerfile"
  context = "."
  target = "base"
  tags = [
    "${REGISTRY}/devcontainer:base-${VERSION}",
    "${REGISTRY}/devcontainer:base-latest"
  ]
  # Use per-target local cache to avoid concurrent writer crashes
  cache-from = [
    "type=local,src=.buildx-cache/base"
  ]
  cache-to = [
    "type=local,dest=.buildx-cache/base,mode=max"
  ]
  platforms = ["linux/amd64", "linux/arm64"]
}

# ============================================================================
# TOOLS TARGET - Development Tools
# ============================================================================
target "tools" {
  dockerfile = "docker/devcontainer/tools.dockerfile"
  context = "."
  target = "tools"
  contexts = {
    spec-kit-base = "target:base"
  }
  tags = [
    "${REGISTRY}/devcontainer:tools-${VERSION}",
    "${REGISTRY}/devcontainer:tools-latest"
  ]
  cache-from = [
    "type=local,src=.buildx-cache/tools"
  ]
  cache-to = [
    "type=local,dest=.buildx-cache/tools,mode=max"
  ]
  platforms = ["linux/amd64", "linux/arm64"]
}

# ============================================================================
# DEVELOPMENT TARGET - Final Development Environment
# ============================================================================
target "development" {
  dockerfile = "docker/devcontainer/development.dockerfile"
  context = "."
  target = "development"
  contexts = {
    spec-kit-tools = "target:tools"
  }
  tags = [
    "${REGISTRY}/devcontainer:dev-${VERSION}",
    "${REGISTRY}/devcontainer:latest"
  ]
  cache-from = [
    "type=local,src=.buildx-cache/development"
  ]
  cache-to = [
    "type=local,dest=.buildx-cache/development,mode=max"
  ]
  platforms = ["linux/amd64", "linux/arm64"]
  args = {
    BUILDKIT_INLINE_CACHE = "1"
    DOCKER_BUILDKIT = "1"
  }
}

# ============================================================================
# PLAYWRIGHT TARGET - E2E Testing
# ============================================================================
target "playwright" {
  dockerfile = "docker/dockerfiles/playwright.Dockerfile"
  context = "."
  tags = [
    "${REGISTRY}/playwright:${VERSION}",
    "${REGISTRY}/playwright:latest"
  ]
  cache-from = [
    "type=local,src=.buildx-cache/playwright"
  ]
  cache-to = [
    "type=local,dest=.buildx-cache/playwright,mode=max"
  ]
  platforms = ["linux/amd64"]
}

# ============================================================================
# GROUP DEFINITIONS
# ============================================================================
group "default" {
  targets = ["development"]
}

group "all" {
  targets = ["base", "tools", "development"]
}

group "ci" {
  targets = ["development"]
}

# ============================================================================
# PERFORMANCE TARGETS
# ============================================================================
target "cache-prewarm" {
  target = "base"
  dockerfile = "docker/devcontainer/base.dockerfile" # fixed path
  context = "."
  cache-to = [
    "type=gha,mode=max",
    "type=registry,ref=${REGISTRY}/devcontainer:cache-prewarm,mode=max"
  ]
  output = ["type=cacheonly"]
}

target "local" {
  inherits = ["development"]
  output = ["type=docker"]
  tags = ["spec-kit-devcontainer:local"]
  # Force single-platform for docker exporter
  platforms = ["linux/amd64"]
  # Separate cache to avoid clashes
  cache-from = [
    "type=local,src=.buildx-cache/local"
  ]
  cache-to = [
    "type=local,dest=.buildx-cache/local,mode=max"
  ]
}
