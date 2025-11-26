# syntax=docker/dockerfile:1.4
# Optimized Development Container - Multi-Stage Build Architecture
# Stage 1: Base system setup with essential tools

FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm as base

# ============================================================================
# BUILD ARGUMENTS & PERFORMANCE CONFIGURATION
# ============================================================================
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID
ARG BUILDKIT_INLINE_CACHE=1

# Performance optimization labels for better cache management
LABEL org.opencontainers.image.title="spec-kit-devcontainer"
LABEL org.opencontainers.image.description="Optimized development container for spec-kit"
LABEL cache.version="2.0"
LABEL performance.optimized="true"

# ============================================================================
# STAGE 1: BASE SYSTEM OPTIMIZATION & APT CONFIGURATION
# ============================================================================
# Configure apt for maximum caching and performance
RUN rm -f /etc/apt/apt.conf.d/docker-clean \
  && echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache \
  && echo 'APT::Install-Recommends "false";' >> /etc/apt/apt.conf.d/no-recommends \
  && echo 'APT::Install-Suggests "false";' >> /etc/apt/apt.conf.d/no-suggests \
  && echo 'Acquire::Retries "3";' >> /etc/apt/apt.conf.d/retries \
  && echo 'Acquire::http::Timeout "30";' >> /etc/apt/apt.conf.d/timeout \
  && echo 'Acquire::CompressionTypes::Order:: "gz";' >> /etc/apt/apt.conf.d/compression

# Install essential system packages with maximum caching
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt,sharing=locked \
  set -eux; \
  apt-get update \
  && export DEBIAN_FRONTEND=noninteractive \
  && apt-get -y install --no-install-recommends \
  # Essential build tools
  build-essential \
  ca-certificates \
  gnupg \
  lsb-release \
  # XML processing tools
  libxml2-utils \
  xmlstarlet \
  # Network tools
  curl \
  wget \
  git \
  openssh-client \
  # Development utilities
  vim-tiny \
  nano \
  htop \
  tree \
  jq \
  # Performance tools
  parallel \
  rsync \
  # Network performance tools
  iputils-ping \
  dnsutils \
  # Compression tools
  xz-utils \
  gzip \
  zstd \
  && apt-get autoremove -y \
  && apt-get clean

# ============================================================================
# STAGE 2: TOOLS & DEPENDENCY INSTALLATION
# ============================================================================
FROM base as tools

# ============================================================================
# USER CONFIGURATION & PERMISSION OPTIMIZATION
# ============================================================================
# Configure user with optimized permission handling
RUN set -eux; \
  if [ "${USERNAME}" != "root" ]; then \
  # Batch permission changes for efficiency
  groupmod --gid "$USER_GID" "$USERNAME" \
  && usermod --uid "$USER_UID" --gid "$USER_GID" "$USERNAME" \
  && usermod -aG sudo "$USERNAME"; \
  fi

# ============================================================================
# DEVELOPMENT ENVIRONMENT & CACHE SETUP
# ============================================================================
# Create comprehensive cache directory structure with optimal permissions
RUN set -eux; \
  # Create all cache directories in a single operation
  install -d -o "$USERNAME" -g "$USERNAME" -m 755 \
  "/home/$USERNAME/.npm-cache" \
  "/home/$USERNAME/.yarn-cache" \
  "/home/$USERNAME/.uv-cache" \
  "/home/$USERNAME/.pip-cache" \
  "/home/$USERNAME/.cache" \
  "/home/$USERNAME/.local/share" \
  "/home/$USERNAME/.config" \
  # Create performance monitoring directories
  && install -d -o "$USERNAME" -g "$USERNAME" -m 755 \
  "/home/$USERNAME/.cache/pip" \
  "/home/$USERNAME/.cache/uv" \
  "/home/$USERNAME/.local/bin" \
  # Set up shell optimizations
  && echo 'export HISTSIZE=10000' >> "/home/$USERNAME/.bashrc" \
  && echo 'export HISTFILESIZE=10000' >> "/home/$USERNAME/.bashrc" \
  && echo 'export HISTTIMEFORMAT="%F %T "' >> "/home/$USERNAME/.bashrc" \
  # Add performance aliases
  && echo 'alias ll="ls -la"' >> "/home/$USERNAME/.bashrc" \
  && echo 'alias la="ls -A"' >> "/home/$USERNAME/.bashrc" \
  && echo 'alias l="ls -CF"' >> "/home/$USERNAME/.bashrc"

# ============================================================================
# PYTHON ENVIRONMENT & DEPENDENCY OPTIMIZATION
# ============================================================================
# Install and cache Python dependencies with maximum efficiency
COPY docker/prewarm /tmp/prewarm
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
  --mount=type=cache,target=/home/$USERNAME/.cache/pip,sharing=locked \
  --mount=type=cache,target=/root/.cache/uv,sharing=locked \
  set -eux; \
  cd /tmp/prewarm \
  # Install with comprehensive caching and optimization
  && export PIP_CACHE_DIR="/root/.cache/pip" \
  && export UV_CACHE_DIR="/root/.cache/uv" \
  && export PIP_DISABLE_PIP_VERSION_CHECK=1 \
  && export PYTHONDONTWRITEBYTECODE=1 \
  # Use UV for faster installation if available, fallback to pip
  && (/root/.local/bin/uv pip install -e . 2>/dev/null || python -m pip install --cache-dir="$PIP_CACHE_DIR" -e .) \
  # Verify installation and cache Python imports
  && python -c "import typer, rich, httpx; print('✓ Prewarm dependencies verified and cached')" \
  # Cleanup temporary files but preserve caches
  && rm -rf /tmp/prewarm \
  # Pre-compile Python bytecode for faster startup
  && python -m compileall /usr/local/lib/python* 2>/dev/null || true

# ============================================================================
# MCP SERVER INTEGRATION & DEVELOPMENT TOOLS
# ============================================================================
# Install MCP servers for integrated development workflow
RUN --mount=type=cache,target=/root/.npm,sharing=locked \
  --mount=type=cache,target=/home/$USERNAME/.npm-cache,sharing=locked \
  set -eux; \
  # Configure npm for optimal performance
  export NPM_CONFIG_CACHE="/root/.npm" \
  && export NPM_CONFIG_UPDATE_NOTIFIER=false \
  && export NPM_CONFIG_FUND=false \
  && export NPM_CONFIG_AUDIT=false \
  # Install MCP servers with caching
  && npm install -g --cache="/root/.npm" \
  @modelcontextprotocol/server-github@latest \
  @modelcontextprotocol/server-filesystem@latest \
  # Verify installations
  && npx --version \
  && npm list -g --depth=0 \
  # Set up npm cache for the vscode user
  && chown -R "$USERNAME:$USERNAME" "/home/$USERNAME/.npm-cache" 2>/dev/null || true

# ============================================================================
# PERFORMANCE OPTIMIZATION & ENVIRONMENT CONFIGURATION
# ============================================================================
# Configure optimal development environment variables
ENV \
  # Python optimizations
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONIOENCODING=utf-8 \
  PIP_NO_CACHE_DIR=0 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PIP_CACHE_DIR=/home/vscode/.pip-cache \
  # UV optimizations
  UV_NO_EMOJI=1 \
  UV_CACHE_DIR=/home/vscode/.uv-cache \
  UV_LINK_MODE=copy \
  # Node.js optimizations
  NPM_CONFIG_UPDATE_NOTIFIER=false \
  NPM_CONFIG_FUND=false \
  NPM_CONFIG_AUDIT=false \
  NPM_CONFIG_CACHE=/home/vscode/.npm-cache \
  # Development optimizations
  DEBIAN_FRONTEND=noninteractive \
  # Build performance
  MAKEFLAGS="-j$(nproc)" \
  # SSD optimizations
  TMPDIR=/tmp \
  # Shell optimizations
  HISTSIZE=10000 \
  HISTFILESIZE=10000 \
  # Performance monitoring
  ENABLE_BUILD_STATS=1

# Add performance optimization tools to PATH
ENV PATH="/root/.local/bin:/home/$USERNAME/.local/bin:$PATH"

# ============================================================================
# FINAL OPTIMIZATIONS & USER SWITCH
# ============================================================================
# Final system optimizations and cleanup
RUN set -eux; \
  # Configure system for optimal SSD performance
  echo 'vm.swappiness=1' >> /etc/sysctl.conf \
  && echo 'vm.vfs_cache_pressure=50' >> /etc/sysctl.conf \
  # Set up efficient file system operations
  && echo 'fs.file-max=2097152' >> /etc/sysctl.conf \
  # Configure optimal I/O scheduler (if not already set by host)
  && echo 'deadline' > /sys/block/*/queue/scheduler 2>/dev/null || true \
  # Final cleanup to minimize layer size
  && find /tmp -type f -delete 2>/dev/null || true \
  && find /var/tmp -type f -delete 2>/dev/null || true \
  # Pre-create common directories to avoid runtime overhead
  && mkdir -p /workspaces /workspace \
  && chown "$USERNAME:$USERNAME" /workspaces /workspace

# Health check for container optimization verification
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python3 -c "import sys; print('✓ Python OK'); sys.exit(0)" && \
  npx --version > /dev/null && \
  echo "✓ Container healthy and optimized"

# Switch to non-root user for security and consistency
USER $USERNAME

# Set optimized working directory
WORKDIR /workspaces
