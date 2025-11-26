# Multi-stage build for Embeddings Service
# Optimized for minimal size and fast startup with volume persistence
# PRECOMPILED: All dependencies baked in

# Stage 1: Base with dependencies
FROM python:3.13-slim AS base

WORKDIR /app

# Install build dependencies (slim uses apt, not apk)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

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
FROM python:3.13-slim AS runtime

WORKDIR /app

# Create non-root user for security
RUN groupadd -r -g 1001 appuser && \
    useradd -r -u 1001 -g appuser appuser

# Install wget for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends wget && \
    rm -rf /var/lib/apt/lists/*

# Copy Python packages from base
COPY --from=base /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=base /usr/local/bin /usr/local/bin

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
