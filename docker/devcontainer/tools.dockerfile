# syntax=docker/dockerfile:1.4
# Tools Development Container - Python/Node.js Tools
FROM spec-kit-base as tools

USER root

# ============================================================================
# PYTHON TOOLS INSTALLATION WITH AGGRESSIVE CACHING
# ============================================================================
# Create requirements file for consistent tool installation
RUN echo '# Core Python development tools' > /tmp/dev-requirements.txt && \
    echo 'flake8==7.1.1' >> /tmp/dev-requirements.txt && \
    echo 'autopep8==2.3.1' >> /tmp/dev-requirements.txt && \
    echo 'black==24.10.0' >> /tmp/dev-requirements.txt && \
    echo 'yapf==0.40.2' >> /tmp/dev-requirements.txt && \
    echo 'mypy==1.13.0' >> /tmp/dev-requirements.txt && \
    echo 'pydocstyle==6.3.0' >> /tmp/dev-requirements.txt && \
    echo 'pycodestyle==2.12.1' >> /tmp/dev-requirements.txt && \
    echo 'bandit==1.8.0' >> /tmp/dev-requirements.txt && \
    echo 'pipenv==2024.4.0' >> /tmp/dev-requirements.txt && \
    echo 'virtualenv==20.27.1' >> /tmp/dev-requirements.txt && \
    echo 'pytest==8.3.3' >> /tmp/dev-requirements.txt && \
    echo 'pylint==3.3.1' >> /tmp/dev-requirements.txt && \
    echo 'ruff==0.8.4' >> /tmp/dev-requirements.txt && \
    echo 'pyyaml==6.0.2' >> /tmp/dev-requirements.txt && \
    echo 'uv==0.5.4' >> /tmp/dev-requirements.txt && \
    echo 'build==1.2.2' >> /tmp/dev-requirements.txt && \
    echo 'wheel==0.45.1' >> /tmp/dev-requirements.txt && \
    echo 'setuptools==75.6.0' >> /tmp/dev-requirements.txt && \
    echo 'setuptools-scm==8.1.0' >> /tmp/dev-requirements.txt && \
    echo 'pip-tools==7.4.1' >> /tmp/dev-requirements.txt && \
    echo 'pre-commit==4.0.1' >> /tmp/dev-requirements.txt

# Install Python tools with cache optimization
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    --mount=type=cache,target=/home/vscode/.cache/pip,sharing=locked \
    set -eux; \
    pip install --upgrade pip setuptools wheel \
    && pip install -r /tmp/dev-requirements.txt --cache-dir /root/.cache/pip \
    && rm /tmp/dev-requirements.txt

# ---------------------------------------------------------------------------
# Python dependency prewarm for instant subsequent builds
# ---------------------------------------------------------------------------
COPY docker/prewarm /tmp/prewarm
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    --mount=type=cache,target=/home/vscode/.cache/pip,sharing=locked \
    --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    set -eux; \
    export PIP_CACHE_DIR="/root/.cache/pip" \
    && export UV_CACHE_DIR="/root/.cache/uv" \
    && export PIP_DISABLE_PIP_VERSION_CHECK=1 \
    && export PYTHONDONTWRITEBYTECODE=1 \
    && cd /tmp/prewarm \
    && (python -m pip install --cache-dir="$PIP_CACHE_DIR" -e .) \
    && python -c "import typer, rich, httpx; print('✓ Prewarm dependencies verified and cached')" \
    && rm -rf /tmp/prewarm \
    && python -m compileall /usr/local/lib/python* 2>/dev/null || true

# ============================================================================
# NODE.JS TOOLS & CACHE CONFIGURATION
# ============================================================================
# Configure npm and yarn for optimal performance
RUN --mount=type=cache,target=/root/.npm,sharing=locked \
    --mount=type=cache,target=/home/vscode/.npm,sharing=locked \
    set -eux; \
    if command -v npm >/dev/null 2>&1; then \
    npm config set cache /home/vscode/.npm --global; \
    npm config set fund false --global; \
    npm config set audit false --global; \
    npm config set update-notifier false --global; \
    fi

# ---------------------------------------------------------------------------
# MCP server integration (optional; runs only if npm is available)
# ---------------------------------------------------------------------------
RUN --mount=type=cache,target=/root/.npm,sharing=locked \
    --mount=type=cache,target=/home/vscode/.npm,sharing=locked \
    set -eux; \
    if command -v npm >/dev/null 2>&1; then \
    npm install -g --cache="/root/.npm" \
    @modelcontextprotocol/server-github@latest \
    @modelcontextprotocol/server-filesystem@latest \
    && npx --version \
    && npm list -g --depth=0; \
    fi

# ============================================================================
# DEVELOPMENT TOOL OPTIMIZATION
# ============================================================================
# Configure development environment variables for performance
ENV \
    # Python optimizations
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_CACHE_DIR=/home/vscode/.cache/pip \
    # UV optimizations
    UV_CACHE_DIR=/home/vscode/.cache/uv \
    UV_NO_EMOJI=1 \
    UV_LINK_MODE=copy \
    UV_CONCURRENT_DOWNLOADS=10 \
    UV_HTTP_TIMEOUT=30 \
    # Node.js optimizations
    NPM_CONFIG_CACHE=/home/vscode/.npm \
    YARN_CACHE_FOLDER=/home/vscode/.cache/yarn \
    NODE_OPTIONS="--max-old-space-size=4096" \
    # Build optimizations
    DOCKER_BUILDKIT=1 \
    BUILDKIT_PROGRESS=plain

# Add tools to PATH
ENV PATH="/home/vscode/.local/bin:$PATH"

USER vscode
WORKDIR /workspaces/spec-kit
