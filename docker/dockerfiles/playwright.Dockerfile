FROM mcr.microsoft.com/playwright:v1.57.0-jammy

# Standard Build Arguments
ARG IMAGE_VERSION=latest
ARG BUILD_DATE
ARG BUILDKIT_INLINE_CACHE=1
ARG DOCKER_BUILDKIT=1

# OCI Labels
LABEL org.opencontainers.image.title="spec-kit-playwright"
LABEL org.opencontainers.image.description="Playwright E2E Testing Service"
LABEL org.opencontainers.image.source="https://github.com/github/spec-kit"
LABEL org.opencontainers.image.version="${IMAGE_VERSION}"
LABEL org.opencontainers.image.vendor="GitHub"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL cache.version="1.0"
LABEL performance.optimized="true"

WORKDIR /app

# Copy package files
COPY docker/tests/package.json docker/tests/package-lock.json* ./

# Install dependencies
RUN npm ci

# Install Playwright browsers and dependencies
RUN npx playwright install --with-deps

# Copy test source code
COPY docker/tests/ .

# Set environment variables
ENV CI=true

# Default command to run tests
CMD ["npx", "playwright", "test"]
