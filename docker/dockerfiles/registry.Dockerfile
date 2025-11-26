# Local Docker Registry
# Optimized for local development and build caching
# Based on registry:2

FROM registry:2.8.3

# Standard Build Arguments
ARG VERSION=latest
ARG BUILD_DATE
ARG BUILDKIT_INLINE_CACHE=1
ARG DOCKER_BUILDKIT=1

# OCI Labels
LABEL org.opencontainers.image.title="spec-kit-registry"
LABEL org.opencontainers.image.description="Local Docker registry with caching and garbage collection"
LABEL org.opencontainers.image.source="https://github.com/github/spec-kit"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.vendor="GitHub"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL cache.version="1.0"
LABEL performance.optimized="true"

# Install additional tools for maintenance
USER root

# Create registry user if it doesn't exist
RUN addgroup -g 1000 -S registry 2>/dev/null || true && \
    adduser -S -u 1000 -G registry -h /var/lib/registry registry 2>/dev/null || true

RUN apk add --no-cache \
    curl \
    jq \
    bash \
    ca-certificates

# Create necessary directories
RUN mkdir -p /var/lib/registry \
    && mkdir -p /etc/docker/registry \
    && mkdir -p /var/log/registry

# Copy configuration files (baked in from .config)
COPY .config/docker/registry/config.yml /etc/docker/registry/config.yml
COPY .config/docker/registry/gc-config.yml /etc/docker/registry/gc-config.yml

# Set proper permissions (use numeric IDs to avoid user lookup issues)
RUN chown -R 1000:1000 /var/lib/registry \
    && chown -R 1000:1000 /var/log/registry

# Health check script
COPY --chmod=755 <<'EOF' /usr/local/bin/healthcheck.sh
#!/bin/bash
curl -sf http://localhost:5000/v2/ > /dev/null && exit 0 || exit 1
EOF

# Garbage collection script
COPY --chmod=755 <<'EOF' /usr/local/bin/gc.sh
#!/bin/bash
echo "Starting garbage collection..."
/bin/registry garbage-collect /etc/docker/registry/config.yml
echo "Garbage collection completed."
EOF

# Switch to non-root user (use numeric ID)
USER 1000

# Expose ports
EXPOSE 5000 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

# Volume for registry data
VOLUME ["/var/lib/registry"]

# Default command
CMD ["serve", "/etc/docker/registry/config.yml"]
