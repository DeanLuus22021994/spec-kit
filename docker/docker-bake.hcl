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

variable "COMPOSE_DOCKER_CLI_BUILD" {
  default = "1"
}

variable "TAG" {
  default = "latest"
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

# Groups
group "default" {
  targets = ["backend", "frontend", "engine", "database", "redis", "embeddings"]
}

group "core" {
  targets = ["backend", "database", "redis"]
}

# Targets
target "backend" {
  context = "."
  dockerfile = "dockerfiles/backend.Dockerfile"
  tags = ["spec-kit/backend:${TAG}"]
  platforms = ["linux/amd64", "linux/arm64"]
  cache-from = ["type=local,src=.buildx-cache/backend"]
  cache-to = ["type=local,dest=.buildx-cache/backend,mode=max"]
}

target "frontend" {
  context = "."
  dockerfile = "dockerfiles/frontend.Dockerfile"
  tags = ["spec-kit/frontend:${TAG}"]
  platforms = ["linux/amd64", "linux/arm64"]
  cache-from = ["type=local,src=.buildx-cache/frontend"]
  cache-to = ["type=local,dest=.buildx-cache/frontend,mode=max"]
}

target "engine" {
  context = "."
  dockerfile = "dockerfiles/engine.Dockerfile"
  tags = ["spec-kit/engine:${TAG}"]
  platforms = ["linux/amd64", "linux/arm64"]
  cache-from = ["type=local,src=.buildx-cache/engine"]
  cache-to = ["type=local,dest=.buildx-cache/engine,mode=max"]
}

target "database" {
  context = "."
  dockerfile = "dockerfiles/database.Dockerfile"
  tags = ["spec-kit/database:${TAG}"]
  platforms = ["linux/amd64", "linux/arm64"]
  cache-from = ["type=local,src=.buildx-cache/database"]
  cache-to = ["type=local,dest=.buildx-cache/database,mode=max"]
}

target "redis" {
  context = "."
  dockerfile = "dockerfiles/redis.Dockerfile"
  tags = ["spec-kit/redis:${TAG}"]
  platforms = ["linux/amd64", "linux/arm64"]
  cache-from = ["type=local,src=.buildx-cache/redis"]
  cache-to = ["type=local,dest=.buildx-cache/redis,mode=max"]
}

target "embeddings" {
  context = "."
  dockerfile = "dockerfiles/embeddings.Dockerfile"
  tags = ["spec-kit/embeddings:${TAG}"]
  platforms = ["linux/amd64", "linux/arm64"]
  cache-from = ["type=local,src=.buildx-cache/embeddings"]
  cache-to = ["type=local,dest=.buildx-cache/embeddings,mode=max"]
}
