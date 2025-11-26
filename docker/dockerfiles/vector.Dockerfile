# Lightweight Qdrant vector database for semantic search
FROM qdrant/qdrant:v1.7.4-unprivileged

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
