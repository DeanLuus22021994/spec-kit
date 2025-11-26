# Multi-stage build for Frontend React App
# Optimized for minimal size and fast startup with volume persistence

# Stage 1: Build
FROM node:20-alpine AS build

# Standard Build Arguments
ARG IMAGE_VERSION=latest
ARG BUILD_DATE
ARG BUILDKIT_INLINE_CACHE=1
ARG DOCKER_BUILDKIT=1

# OCI Labels
LABEL org.opencontainers.image.title="spec-kit-frontend"
LABEL org.opencontainers.image.description="Frontend React App for Semantic Kernel Application"
LABEL org.opencontainers.image.source="https://github.com/github/spec-kit"
LABEL org.opencontainers.image.version="${IMAGE_VERSION}"
LABEL org.opencontainers.image.vendor="GitHub"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL cache.version="1.0"
LABEL performance.optimized="true"

WORKDIR /app

# Copy package files and install dependencies (cached layer)
COPY src/frontend/package*.json ./
RUN npm ci && npm cache clean --force

# Copy source and build
COPY src/frontend/ ./
RUN npm run build

# Stage 2: Runtime with nginx
FROM nginx:1.27-alpine AS runtime

# Create non-root user for nginx
RUN addgroup -g 1001 -S nginx-user && \
    adduser -S nginx-user -u 1001 -G nginx-user

# Copy built assets
COPY --from=build --chown=nginx-user:nginx-user /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY --chown=nginx-user:nginx-user infrastructure/nginx/nginx.conf /etc/nginx/nginx.conf

# Create directories for logs and cache
RUN mkdir -p /var/cache/nginx /var/log/nginx /var/run && \
    chown -R nginx-user:nginx-user /var/cache/nginx /var/log/nginx /var/run /usr/share/nginx/html

# Switch to non-root user
USER nginx-user

# Volume mount points for persistence
VOLUME ["/var/log/nginx", "/var/cache/nginx"]

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

CMD ["nginx", "-g", "daemon off;"]
