# Multi-stage Redis with RedisInsight dashboard
# Optimized for cache layer with persistence and web-based UI

# =====================================================
# Stage 1: Redis Server (Official Alpine)
# =====================================================
FROM redis:7.2-alpine AS redis-server

# Install runtime dependencies
RUN apk add --no-cache \
    bash \
    curl \
    ca-certificates

# Create non-root user
RUN addgroup -g 1001 -S redis-user && \
    adduser -S redis-user -u 1001 -G redis-user

# Create directories for persistence
RUN mkdir -p /data /var/log/redis && \
    chown -R redis-user:redis-user /data /var/log/redis

# Copy custom Redis configuration
COPY infrastructure/redis/redis.conf /usr/local/etc/redis/redis.conf

# Switch to non-root user
USER redis-user

# Volume mount points for persistence
VOLUME ["/data", "/var/log/redis"]

EXPOSE 6379

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD redis-cli ping | grep PONG || exit 1

# Run Redis with custom config
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]
