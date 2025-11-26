# Multi-stage build for Backend API
# Optimized for minimal size and fast startup with volume persistence
# PRECOMPILED: All dependencies baked in

# Stage 1: Build
FROM mcr.microsoft.com/dotnet/sdk:9.0-alpine AS build

# Standard Build Arguments
ARG VERSION=latest
ARG BUILD_DATE
ARG BUILDKIT_INLINE_CACHE=1
ARG DOCKER_BUILDKIT=1

# OCI Labels
LABEL org.opencontainers.image.title="spec-kit-backend"
LABEL org.opencontainers.image.description="Backend API for Semantic Kernel Application"
LABEL org.opencontainers.image.source="https://github.com/github/spec-kit"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.vendor="GitHub"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL cache.version="1.0"
LABEL performance.optimized="true"

WORKDIR /src

# Copy csproj and restore dependencies (cached layer)
COPY src/engine/engine.csproj ./engine/
COPY src/business/business.csproj ./business/
COPY src/backend/backend.csproj ./backend/
COPY src/Directory.Packages.props ./Directory.Packages.props
RUN dotnet restore ./backend/backend.csproj

# Copy source and build
COPY src/engine/ ./engine/
COPY src/business/ ./business/
COPY src/backend/ ./backend/
WORKDIR /src/backend
RUN dotnet publish backend.csproj -c Release -o /app/publish --no-restore

# Stage 2: Runtime
FROM mcr.microsoft.com/dotnet/aspnet:9.0-alpine AS runtime

WORKDIR /app

# Install ICU libraries for globalization support and wget for healthchecks
RUN apk add --no-cache icu-libs icu-data-full wget

# Create non-root user for security
RUN addgroup -g 1001 -S appuser && \
    adduser -S appuser -u 1001 -G appuser

# Create directories for persistent volumes
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appuser /app

# Copy published output
COPY --from=build --chown=appuser:appuser /app/publish .

# Switch to non-root user
USER appuser

# Set environment variables
ENV ASPNETCORE_URLS=http://+:80 \
    DOTNET_RUNNING_IN_CONTAINER=true \
    DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=false

# Volume mount points for persistence
VOLUME ["/app/logs", "/app/data"]

EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/health || exit 1

ENTRYPOINT ["dotnet", "backend.dll"]
