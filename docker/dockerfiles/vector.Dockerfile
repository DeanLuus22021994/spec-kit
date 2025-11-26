# Lightweight Qdrant vector database for semantic search
FROM qdrant/qdrant:v1.7.4-unprivileged

# Standard Build Arguments
ARG VERSION=latest
ARG BUILD_DATE
ARG BUILDKIT_INLINE_CACHE=1
ARG DOCKER_BUILDKIT=1

# OCI Labels
LABEL org.opencontainers.image.title="spec-kit-vector"
LABEL org.opencontainers.image.description="Qdrant Vector Database for Semantic Kernel Application"
LABEL org.opencontainers.image.source="https://github.com/github/spec-kit"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.vendor="GitHub"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL cache.version="1.0"
LABEL performance.optimized="true"

# Copy vector configuration
COPY semantic/vector/.config/config.yml /qdrant/config/production.yaml

# Create storage directories and install wget for healthchecks
USER root
RUN apt-get update && apt-get install -y --no-install-recommends wget && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /qdrant/storage /qdrant/snapshots && \
    chown -R qdrant:qdrant /qdrant

USER qdrant

EXPOSE 6333 6334

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:6333/healthz || exit 1

CMD ["./qdrant", "--config-path", "/qdrant/config/production.yaml"]
