# =====================================================
# PostgreSQL 16 Database with Semantic Kernel Support
# =====================================================
# Features:
# - pgvector extension for embeddings
# - Automated migrations on startup
# - Environment-aware seed data loading
# - Backup/restore scripts
# - Optimized configuration for performance
# =====================================================

# Use pgvector-enabled PostgreSQL image
FROM pgvector/pgvector:pg16 AS base

# Standard Build Arguments
ARG VERSION=latest
ARG BUILD_DATE
ARG BUILDKIT_INLINE_CACHE=1
ARG DOCKER_BUILDKIT=1

# OCI Labels
LABEL org.opencontainers.image.title="spec-kit-database"
LABEL org.opencontainers.image.description="PostgreSQL database with semantic kernel capabilities and pgvector"
LABEL org.opencontainers.image.source="https://github.com/github/spec-kit"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.vendor="GitHub"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL cache.version="1.0"
LABEL performance.optimized="true"

# =====================================================
# Stage 1: Install Dependencies
# =====================================================

# Install required packages (Debian-based image)
RUN apt-get update && apt-get install -y \
    postgresql-contrib \
    bash \
    coreutils \
    findutils \
    grep \
    sed \
    && rm -rf /var/lib/apt/lists/*

# Install pgvector extension for vector similarity search
# Note: This requires pgvector to be available in the Alpine repositories
# or compiled from source. For production, use prebuilt image or compile.
# For now, we'll note this requirement in documentation.

# =====================================================
# Stage 2: Copy Database Files
# =====================================================

# Create directories for migrations, seeds, and scripts
RUN mkdir -p /migrations /seeds /scripts /backups \
    && chown -R postgres:postgres /migrations /seeds /scripts /backups

# Copy initialization script (runs first on fresh database)
COPY --chown=postgres:postgres infrastructure/database/init.sql /docker-entrypoint-initdb.d/01-init.sql

# Copy migration files
COPY --chown=postgres:postgres infrastructure/database/migrations/*.sql /migrations/

# Copy seed data files
COPY --chown=postgres:postgres infrastructure/database/seeds/*.sql /seeds/

# Copy management scripts
COPY --chown=postgres:postgres infrastructure/database/scripts/*.sh /scripts/
RUN chmod +x /scripts/*.sh && sed -i 's/\r$//' /scripts/*.sh

# =====================================================
# Stage 3: Custom Initialization Script
# =====================================================

# Use precreated initialization wrapper that runs additional migrations and seeds
COPY --chown=postgres:postgres infrastructure/database/scripts/99-run-migrations-and-seeds.sh /docker-entrypoint-initdb.d/99-run-migrations-and-seeds.sh
RUN chmod +x /docker-entrypoint-initdb.d/99-run-migrations-and-seeds.sh && sed -i 's/\r$//' /docker-entrypoint-initdb.d/99-run-migrations-and-seeds.sh

# =====================================================
# Stage 4: Final Configuration
# =====================================================

# Expose PostgreSQL port
EXPOSE 5432

# Create volume mount points
VOLUME ["/var/lib/postgresql/data", "/backups", "/var/log/postgresql"]

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD pg_isready -U ${POSTGRES_USER:-user} -d ${POSTGRES_DB:-semantic_kernel} || exit 1

# PostgreSQL will run with optimizations via command line
# Configuration is applied through docker-compose.yml command option

# Run as postgres user
USER postgres

# Default command (inherited from base image with custom config)
CMD ["postgres", \
    "-c", "shared_buffers=128MB", \
    "-c", "effective_cache_size=256MB", \
    "-c", "work_mem=4MB", \
    "-c", "max_connections=100", \
    "-c", "log_min_duration_statement=1000", \
    "-c", "log_connections=on", \
    "-c", "log_disconnections=on"]
