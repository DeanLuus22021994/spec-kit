# Multi-stage build for GitHub MCP Server
# Optimized for minimal size and fast startup with volume persistence

# Stage 1: Base image with Node.js
FROM node:20-alpine AS base

# Install git and other dependencies needed for GitHub operations
RUN apk add --no-cache \
    git \
    openssh-client \
    ca-certificates \
    && rm -rf /var/cache/apk/*

# Create non-root user for security
RUN addgroup -g 1001 -S mcp && \
    adduser -S mcp -u 1001 -G mcp

# Stage 2: Dependencies
FROM base AS deps

WORKDIR /app

# Copy package files from github-mcp directory
COPY --chown=mcp:mcp dockerfiles/github-mcp/package*.json ./

# Install dependencies with npm install (generates lockfile)
RUN npm install --omit=dev && \
    npm cache clean --force

# Stage 3: Final runtime image
FROM base AS runner

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps --chown=mcp:mcp /app/node_modules ./node_modules

# Copy application code from github-mcp directory
COPY --chown=mcp:mcp dockerfiles/github-mcp/ .

# Create directories for persistent volumes
RUN mkdir -p /app/.cache /app/.git-cache /app/data && \
    chown -R mcp:mcp /app/.cache /app/.git-cache /app/data

# Switch to non-root user
USER mcp

# Set environment variables for caching
ENV NODE_ENV=production \
    NPM_CONFIG_CACHE=/app/.cache \
    GIT_CONFIG_GLOBAL=/app/.git-cache/.gitconfig

# Volume mount points for persistence across builds
VOLUME ["/app/.cache", "/app/.git-cache", "/app/data"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "process.exit(0)"

# Entry point
ENTRYPOINT ["node"]
CMD ["index.js"]
