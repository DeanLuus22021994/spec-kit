# Multi-stage build for Semantic Kernel Engine
# Optimized for minimal size and fast startup with volume persistence
# PRECOMPILED: All dependencies baked in

# Stage 1: Build
FROM mcr.microsoft.com/dotnet/sdk:9.0-jammy AS build

# Standard Build Arguments
ARG IMAGE_VERSION=latest
ARG BUILD_DATE
ARG BUILDKIT_INLINE_CACHE=1
ARG DOCKER_BUILDKIT=1

# OCI Labels
LABEL org.opencontainers.image.title="spec-kit-engine"
LABEL org.opencontainers.image.description="Semantic Kernel Engine"
LABEL org.opencontainers.image.source="https://github.com/github/spec-kit"
LABEL org.opencontainers.image.version="${IMAGE_VERSION}"
LABEL org.opencontainers.image.vendor="GitHub"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL cache.version="1.0"
LABEL performance.optimized="true"

WORKDIR /src

# Copy csproj and restore dependencies (cached layer)
COPY src/engine/engine.csproj ./engine/
COPY src/Directory.Packages.props ./Directory.Packages.props
RUN dotnet restore ./engine/engine.csproj

# Copy source and build
COPY src/engine/ ./engine/
WORKDIR /src/engine
RUN dotnet publish engine.csproj -c Release -o /app/publish --no-restore

# Stage 2: Runtime
FROM mcr.microsoft.com/dotnet/aspnet:9.0-jammy AS runtime

WORKDIR /app

# Install ICU libraries for globalization support
RUN apt-get update && apt-get install -y --no-install-recommends libicu-dev && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r -g 1001 appuser && \
    useradd -r -u 1001 -g appuser appuser

# Create directories for persistent volumes and config
RUN mkdir -p /app/plugins /app/skills /app/cache /app/logs /.config && \
    chown -R appuser:appuser /app /.config

# Copy published output
COPY --from=build --chown=appuser:appuser /app/publish .

# Copy configuration files (baked into image, no host mounts)
COPY --chown=appuser:appuser .config/ /.config/

# Switch to non-root user
USER appuser

# Set environment variables
ENV DOTNET_RUNNING_IN_CONTAINER=true \
    DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=false

# Volume mount points for persistence
VOLUME ["/app/plugins", "/app/skills", "/app/cache", "/app/logs"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD dotnet --info > /dev/null || exit 1

# Keep container running for library access
CMD ["tail", "-f", "/dev/null"]
