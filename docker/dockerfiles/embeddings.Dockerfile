# Multi-stage build for Embeddings Service
# Optimized for minimal size and fast startup with volume persistence
# PRECOMPILED: All dependencies baked in

# Stage 1: Base with dependencies
FROM nvidia/cuda:13.0-cudnn-runtime-ubuntu24.04 AS base

# Standard Build Arguments
ARG VERSION=latest
ARG BUILD_DATE
ARG BUILDKIT_INLINE_CACHE=1
ARG DOCKER_BUILDKIT=1

# OCI Labels
LABEL org.opencontainers.image.title="spec-kit-embeddings"
LABEL org.opencontainers.image.description="Embeddings Service for Semantic Kernel Application"
LABEL org.opencontainers.image.source="https://github.com/github/spec-kit"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.vendor="GitHub"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL cache.version="1.0"
LABEL performance.optimized="true"

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi==0.115.6 \
    uvicorn[standard]==0.34.0 \
    openai==1.82.1 \
    pydantic==2.10.6 \
    pydantic-settings==2.7.1 \
    httpx==0.28.1 \
    python-multipart==0.0.20 \
    asyncpg==0.30.0 \
    pyyaml==6.0.2

# Stage 2: Runtime
FROM nvidia/cuda:13.0-cudnn-runtime-ubuntu24.04 AS runtime

WORKDIR /app

# Create non-root user for security
RUN groupadd -r -g 1001 appuser && \
    useradd -r -u 1001 -g appuser appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    python3 \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from base
COPY --from=base /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy embedding service configuration and application
COPY --chown=appuser:appuser semantic/embeddings/.config/config.yml /app/config/config.yml
COPY --chown=appuser:appuser semantic/embeddings/main.py /app/main.py

# Create directories for persistent volumes
RUN mkdir -p /app/cache /app/logs /app/models && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Volume mount points for persistence
VOLUME ["/app/cache", "/app/logs", "/app/models"]

EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8001/health || exit 1

CMD ["python", "/app/main.py"]
