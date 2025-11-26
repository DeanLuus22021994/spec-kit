# Playwright Tests Container - Baked Dependencies
# Provides isolated environment for E2E tests with zero-latency startup
FROM mcr.microsoft.com/playwright:v1.40.0-jammy AS base

LABEL maintainer="semantic-kernel-app"
LABEL description="Playwright test container with baked npm dependencies"

# Set working directory
WORKDIR /app/tests

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r testsuser && useradd -r -g testsuser -u 1001 testsuser

# Install npm dependencies directly (baked in for zero latency)
RUN npm install -g --no-cache \
    @playwright/test@1.40.0 \
    @types/node@24.10.1 \
    typescript@5.3.0

# Install Playwright browsers with dependencies (baked in)
RUN npx playwright install --with-deps chromium firefox webkit

# Copy test source files
COPY --chown=testsuser:testsuser . .

# Create cache directories with proper permissions
RUN mkdir -p \
    /app/tests/.playwright-cache \
    /app/tests/.npm \
    /app/tests/playwright-report \
    /app/tests/test-results \
    /app/tests/node_modules \
    && chown -R testsuser:testsuser /app/tests

# Switch to non-root user
USER testsuser

# Set environment variables
ENV CI=true
ENV NODE_ENV=test
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV NODE_OPTIONS="--max-old-space-size=4096"

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node --version && npx playwright --version

# Default command
CMD ["npx", "playwright", "test"]

# ---
# Stage for debugging/development
FROM base AS dev

USER root
# Install development tools
RUN npm install -g --no-cache \
    nodemon

USER testsuser

ENV CI=false
ENV NODE_ENV=development

CMD ["npx", "playwright", "test", "--ui"]

# ---
# Stage for CI/production
FROM base AS ci

ENV CI=true
ENV NODE_ENV=test

CMD ["npx", "playwright", "test", "--reporter=html", "--reporter=junit"]
