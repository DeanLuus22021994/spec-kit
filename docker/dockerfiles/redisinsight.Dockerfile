# RedisInsight - Official Redis GUI for development
# Lightweight web-based dashboard for Redis management

FROM redis/redisinsight:2.58.0

# Create non-root user
USER root
RUN addgroup -g 1001 redisinsight-user && \
    adduser -u 1001 -G redisinsight-user -s /bin/sh -D redisinsight-user

# Create directories for persistence
RUN mkdir -p /data /var/log/redisinsight /db && \
    chown -R redisinsight-user:redisinsight-user /data /var/log/redisinsight /db

# Switch to non-root user
USER redisinsight-user

# Volume mount points
VOLUME ["/data", "/var/log/redisinsight"]

EXPOSE 5540

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:5540/healthcheck/ || exit 1

CMD ["node", "/usr/src/app/api/dist/src/main"]
