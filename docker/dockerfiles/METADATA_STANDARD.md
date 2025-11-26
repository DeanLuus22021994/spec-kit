# Dockerfile Metadata & Configuration Standard

This document defines the standard pattern for all Dockerfiles in the `spec-kit` repository. All Dockerfiles must adhere to these standards to ensure consistency, OCI compliance, and build optimization.

## 1. OCI Labels

All Dockerfiles must include the following OCI-compliant labels. Replace placeholders with appropriate values.

```dockerfile
LABEL org.opencontainers.image.title="<Service Name>"
LABEL org.opencontainers.image.description="<Service Description>"
LABEL org.opencontainers.image.source="https://github.com/github/spec-kit"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.vendor="GitHub"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL cache.version="1.0"
LABEL performance.optimized="true"
```

## 2. Build Arguments

All Dockerfiles must accept the following build arguments to enable BuildKit features and versioning.

```dockerfile
ARG VERSION=latest
ARG BUILD_DATE
ARG BUILDKIT_INLINE_CACHE=1
ARG DOCKER_BUILDKIT=1
```

## 3. Configuration Injection

Configuration files should be "baked in" to the image from the `docker/.config` directory. Do not rely on host volume mounts for default configuration.

```dockerfile
# Copy configuration (baked into image)
COPY docker/.config/docker/<service>/ /etc/<service>/
```

## 4. Dependency Baking

All dependencies (npm packages, python packages, system libraries) must be installed during the build process. The image should be self-contained and runnable without internet access or volume mounts.

## 5. Volume Mounts

Define `VOLUME` instructions for all directories that require persistence (logs, data, cache).

```dockerfile
VOLUME ["/app/logs", "/app/data"]
```

## 6. User Security

Always run the application as a non-root user.

```dockerfile
RUN addgroup -g 1001 -S appuser && \
    adduser -S appuser -u 1001 -G appuser
USER appuser
```

## 7. Health Checks

Include a `HEALTHCHECK` instruction for all services.

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:<port>/health || exit 1
```
