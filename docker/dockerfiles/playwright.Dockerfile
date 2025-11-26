FROM mcr.microsoft.com/playwright:v1.57.0-jammy

WORKDIR /app

# Copy package files
COPY docker/tests/package.json docker/tests/package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy test source code
COPY docker/tests/ .

# Set environment variables
ENV CI=true

# Default command to run tests
CMD ["npx", "playwright", "test"]
