# Python Tools Container - Slim
# Provides isolated environment for CLI tools, documentation generation, and code quality checks

# Stage 1: Extract Kantra CLI binary from official image
FROM quay.io/konveyor/kantra:latest AS kantra-binary

# Use Python 3.11 to match project requirements
FROM python:3.11-slim

LABEL maintainer="semantic-kernel-app"
LABEL description="Python tools container for CLI, documentation, and code quality"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app/tools

# Install system dependencies
# git: for version control and pip git installs
# curl: for downloading tools
# build-essential: for compiling python extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    maven \
    default-jdk \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r toolsuser && useradd -r -g toolsuser -u 1001 toolsuser

# Copy Kantra CLI binary and dependencies from extraction stage
COPY --from=kantra-binary /usr/local/bin/kantra /usr/local/bin/kantra
COPY --from=kantra-binary /usr/local/bin/konveyor-analyzer /usr/local/bin/konveyor-analyzer
COPY --from=kantra-binary /usr/local/bin/konveyor-analyzer-dep /usr/local/bin/konveyor-analyzer-dep
COPY --from=kantra-binary /usr/local/bin/generic-external-provider /usr/local/bin/generic-external-provider
COPY --from=kantra-binary /usr/local/bin/java-external-provider /usr/local/bin/java-external-provider
COPY --from=kantra-binary /usr/local/bin/yq-external-provider /usr/local/bin/yq-external-provider
COPY --from=kantra-binary /usr/local/bin/golang-dependency-provider /usr/local/bin/golang-dependency-provider

RUN chmod +x /usr/local/bin/kantra \
    /usr/local/bin/konveyor-analyzer \
    /usr/local/bin/konveyor-analyzer-dep \
    /usr/local/bin/generic-external-provider \
    /usr/local/bin/java-external-provider \
    /usr/local/bin/yq-external-provider \
    /usr/local/bin/golang-dependency-provider

# Create and activate virtual environment
RUN python -m venv $VIRTUAL_ENV && \
    chown -R toolsuser:toolsuser $VIRTUAL_ENV

# Install Python dependencies into the virtual environment
# Core CLI dependencies
# Dev/Test dependencies
# Documentation dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    # Core
    typer \
    rich \
    httpx[socks] \
    platformdirs \
    readchar \
    truststore>=0.10.4 \
    PyYAML \
    requests \
    click \
    python-dotenv \
    colorlog \
    # AI/Vector
    openai \
    qdrant-client \
    # Database
    psycopg2-binary \
    # Quality/Linting
    ruff \
    black \
    isort \
    mypy \
    pre-commit \
    sqlfluff \
    shellcheck-py \
    # Testing
    pytest \
    pytest-cov \
    # Documentation
    mkdocs \
    mkdocs-material \
    mkdocs-minify-plugin \
    mkdocs-git-revision-date-localized-plugin

# Copy tools scripts
COPY cli.py docgen.py ./
COPY .config/scripts/ ./.config/scripts/

# Copy validation rules and configuration
COPY .config/validation/rules/ ./.config/validation/rules/
COPY .config/validation/profiles/ ./.config/validation/profiles/
COPY .config/validation/schemas/ ./.config/validation/schemas/
COPY .config/validation/core/ ./.config/validation/core/

# Create directories for caches and reports
RUN mkdir -p /app/tools/.mypy_cache \
    /app/tools/.pytest_cache \
    /app/tools/__pycache__ \
    /app/tools/.config/validation/reports \
    /app/tools/.config/validation/test-data \
    && chown -R toolsuser:toolsuser /app/tools

# Volume definitions
VOLUME /app/tools/.mypy_cache
VOLUME /app/tools/.pytest_cache
VOLUME /app/tools/.config/validation/reports
VOLUME /app/tools/.config/validation/test-data

# Switch to non-root user
USER toolsuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
CMD ["python", "cli.py", "--help"]
