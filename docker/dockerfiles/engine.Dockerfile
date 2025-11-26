# Multi-stage build for Semantic Kernel Engine
# Optimized for minimal size and fast startup with volume persistence
# PRECOMPILED: All dependencies baked in

# Stage 1: Build
FROM mcr.microsoft.com/dotnet/sdk:9.0-alpine AS build

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
FROM mcr.microsoft.com/dotnet/aspnet:9.0-alpine AS runtime

WORKDIR /app

# Install ICU libraries for globalization support
RUN apk add --no-cache icu-libs icu-data-full

# Create non-root user for security
RUN addgroup -g 1001 -S appuser && \
    adduser -S appuser -u 1001 -G appuser

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
