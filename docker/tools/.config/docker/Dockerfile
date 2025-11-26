# Python Tools Container - Slim
# Provides isolated environment for CLI tools, documentation generation, and code quality checks

# Stage 1: Extract Kantra CLI binary from official image
FROM quay.io/konveyor/kantra:latest AS kantra-binary

# Use Python 3.11 to match project requirements
FROM python:3.11-slim

LABEL maintainer="semantic-kernel-app"
LABEL description="Python tools container for CLI, documentation, and code quality"

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
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r toolsuser && useradd -r -g toolsuser -u 1001 toolsuser

# Copy Kantra CLI binary from extraction stage
COPY --from=kantra-binary /usr/local/bin/kantra /usr/local/bin/kantra
RUN chmod +x /usr/local/bin/kantra

# Install Python dependencies
# Core CLI dependencies
# Dev/Test dependencies
# Documentation dependencies
RUN pip install --no-cache-dir \
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

# Set Python to run in unbuffered mode
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/home/toolsuser/.local/bin:${PATH}"

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
CMD ["python", "cli.py", "--help"]
