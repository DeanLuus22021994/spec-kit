# syntax=docker/dockerfile:1.4
# Base Development Container - Minimal System Setup
FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm as base

# ============================================================================
# BUILD ARGUMENTS & PERFORMANCE CONFIGURATION
# ============================================================================
ARG BUILDKIT_INLINE_CACHE=1
ARG DOCKER_BUILDKIT=1

# Performance optimization labels for better cache management
LABEL org.opencontainers.image.title="spec-kit-base"
LABEL org.opencontainers.image.description="Base development container for spec-kit"
LABEL cache.version="1.0"
LABEL performance.optimized="true"

# ============================================================================
# SYSTEM OPTIMIZATION & APT CONFIGURATION
# ============================================================================
# Configure apt for maximum caching and performance
RUN rm -f /etc/apt/apt.conf.d/docker-clean \
    && echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache \
    && echo 'APT::Install-Recommends "false";' >> /etc/apt/apt.conf.d/no-recommends \
    && echo 'APT::Install-Suggests "false";' >> /etc/apt/apt.conf.d/no-suggests \
    && echo 'Acquire::Retries "3";' >> /etc/apt/apt.conf.d/retries \
    && echo 'Acquire::http::Timeout "30";' >> /etc/apt/apt.conf.d/timeout \
    && echo 'Acquire::CompressionTypes::Order:: "gz";' >> /etc/apt/apt.conf.d/compression

# Updated caching strategy for optimal performance
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    set -eux; \
    apt-get update \
    && export DEBIAN_FRONTEND=noninteractive \
    # Install packages in groups by functionality for better cache utilization
    && apt-get -y install --no-install-recommends \
      build-essential ca-certificates gnupg lsb-release \
    && apt-get -y install --no-install-recommends \
      libxml2-utils xmlstarlet \
    && apt-get -y install --no-install-recommends \
      curl wget git openssh-client \
    && apt-get -y install --no-install-recommends \
      vim-tiny nano htop tree jq shellcheck \
    && apt-get -y install --no-install-recommends \
      parallel rsync \
    && apt-get -y install --no-install-recommends \
      xz-utils gzip zstd \
    && apt-get autoremove -y \
    && apt-get clean

# ============================================================================
# USER CONFIGURATION & CACHE SETUP
# ============================================================================
# Create comprehensive cache directory structure
RUN set -eux; \
    mkdir -p \
    /home/vscode/.cache/uv \
    /home/vscode/.cache/pip \
    /home/vscode/.npm \
    /home/vscode/.cache/yarn \
    /home/vscode/.cache/go-build \
    /home/vscode/.docker \
    /home/vscode/.local/bin \
    && chown -R vscode:vscode /home/vscode/.cache /home/vscode/.npm /home/vscode/.docker /home/vscode/.local \
    && chmod 755 /home/vscode/.cache /home/vscode/.npm /home/vscode/.docker /home/vscode/.local

# Switch to non-root user for subsequent operations
USER vscode
WORKDIR /workspaces/spec-kit
