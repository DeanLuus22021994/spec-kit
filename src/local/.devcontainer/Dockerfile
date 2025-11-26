# Use the official Python 3.13 image which supports free-threading (experimental)
# We use the Microsoft devcontainer image for better VS Code integration
FROM mcr.microsoft.com/devcontainers/python:3.13

# Install uv for high-performance package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install additional OS packages for performance and development
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    build-essential \
    cmake \
    ninja-build \
    pkg-config \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Enable Python 3.13 experimental JIT if available (configuration)
# ENV PYTHON_JIT=1

# Set up a non-root user (vscode is created by the base image)
USER vscode

# Configure uv to use system python or create venvs in the project
ENV UV_LINK_MODE=copy

# Set the working directory
WORKDIR /workspaces/local
