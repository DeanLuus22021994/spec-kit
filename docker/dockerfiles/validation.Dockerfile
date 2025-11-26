# Multi-stage Dockerfile for YAML Validation Service
# Integrates Kantra CLI with validation framework for containerized rule enforcement

# Metadata for tracking and documentation
# Version: 1.0.0
# Category: validation
# Keywords: kantra, mta, yaml-validation, podman, docker
# Updated: 2025-11-25

# Stage 1: Extract Kantra CLI binary from official Konveyor image
FROM quay.io/konveyor/kantra:latest AS kantra-source

# Stage 2: Build Python validation framework
# Using Python 3.13-slim for C extension compatibility (asyncpg, pydantic-core)
FROM python:3.13-slim AS builder

LABEL maintainer="semantic-kernel-app"
LABEL description="YAML validation service with Kantra CLI and MTA rules"
LABEL version="1.0.0"

# Set working directory
WORKDIR /workspace

# Install system dependencies
# Podman is required for Kantra hybrid mode (analyzer-lsp containers)
# For containerless mode (--run-local), Podman is optional
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    git \
    curl \
    ca-certificates \
    podman \
    fuse-overlayfs \
    slirp4netns \
    && rm -rf /var/lib/apt/lists/*

# Copy Kantra binary from extraction stage
COPY --from=kantra-source /usr/local/bin/kantra /usr/local/bin/kantra
RUN chmod +x /usr/local/bin/kantra

# Verify Kantra installation (kantra uses 'help' instead of '--version')
RUN kantra help

# Create non-root user for security
RUN groupadd -r toolsuser && useradd -r -g toolsuser -u 1001 -m -s /bin/bash toolsuser

# Configure Podman for rootless operation
RUN mkdir -p /home/toolsuser/.config/containers && \
    chown -R toolsuser:toolsuser /home/toolsuser/.config

# Copy Podman storage configuration
RUN echo '[storage]' > /etc/containers/storage.conf && \
    echo 'driver = "overlay"' >> /etc/containers/storage.conf && \
    echo '[storage.options.overlay]' >> /etc/containers/storage.conf && \
    echo 'mount_program = "/usr/bin/fuse-overlayfs"' >> /etc/containers/storage.conf

# Install Python dependencies for validation framework
COPY tools/.config/validation/requirements.txt /workspace/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for reporting and CLI
RUN pip install --no-cache-dir \
    click>=8.1.7 \
    rich>=13.7.0 \
    colorlog>=6.8.2 \
    jinja2>=3.1.2 \
    tabulate>=0.9.0

# Copy validation framework (baked dependencies - zero file copy latency)
COPY --chown=toolsuser:toolsuser tools/.config/validation/rules/ /workspace/.config/validation/rules/
COPY --chown=toolsuser:toolsuser tools/.config/validation/profiles/ /workspace/.config/validation/profiles/
COPY --chown=toolsuser:toolsuser tools/.config/validation/schemas/ /workspace/.config/validation/schemas/
COPY --chown=toolsuser:toolsuser tools/.config/validation/core/ /workspace/.config/validation/core/

# Copy automation scripts
COPY --chown=toolsuser:toolsuser tools/.config/scripts/validate-yaml.sh /usr/local/bin/validate-yaml
RUN chmod +x /usr/local/bin/validate-yaml

# Create directories with proper permissions
RUN mkdir -p \
    /workspace/.config/validation/reports \
    /workspace/.config/validation/test-data \
    /workspace/.local/share/containers \
    /workspace/.cache/kantra \
    && chown -R toolsuser:toolsuser /workspace

# Switch to non-root user
USER toolsuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HOME=/home/toolsuser
ENV XDG_RUNTIME_DIR=/workspace/.local/share/containers

# Configure default validation mode
# Options: local (containerless, fastest), hybrid (uses analyzer-lsp containers)
ENV RUN_MODE=local
ENV PROFILE=recommended

# Health check - verify Kantra is accessible
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD kantra help >/dev/null 2>&1 || exit 1

# Set working directory for analysis
WORKDIR /workspace

# Default entrypoint uses validate-yaml script
ENTRYPOINT ["validate-yaml"]

# Default command runs recommended profile
CMD ["--profile=recommended"]
