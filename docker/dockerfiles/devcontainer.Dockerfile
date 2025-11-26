# Minimal devcontainer Dockerfile for this workspace
# Based on Ubuntu, installs common developer tools used by the repo
FROM mcr.microsoft.com/devcontainers/base:ubuntu

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    wget \
    ca-certificates \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    unzip \
    locales \
    && rm -rf /var/lib/apt/lists/*

RUN locale-gen en_US.UTF-8 || true
ENV LANG=en_US.UTF-8

# Install docker CLI (optional for local workflows)
RUN curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-20.10.24.tgz | tar -xzC /tmp \
    && mv /tmp/docker/* /usr/local/bin/ \
    || true

# Ensure pip up-to-date
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Install useful Python tools referenced by repo tooling
RUN python3 -m pip install --no-cache-dir pylint pre-commit

WORKDIR /workspace

CMD ["/bin/bash"]
# Development container with all tools
# PRECOMPILED: All dependencies baked in
FROM mcr.microsoft.com/dotnet/sdk:9.0

# Install Node.js and Python
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Install Python 3.12 and pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Install development tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    vim \
    nano \
    postgresql-client \
    redis-tools \
    jq \
    shellcheck \
    && rm -rf /var/lib/apt/lists/*

# Install global npm packages
RUN npm install -g typescript ts-node nodemon eslint prettier

# Create non-root user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN apt-get update && apt-get install -y sudo \
    && if getent group $USER_GID; then \
    groupmod -n $USERNAME $(getent group $USER_GID | cut -d: -f1); \
    else \
    groupadd --gid $USER_GID $USERNAME; \
    fi \
    && if id -u $USER_UID > /dev/null 2>&1; then \
    usermod -l $USERNAME -d /home/$USERNAME -m $(id -nu $USER_UID); \
    else \
    useradd --uid $USER_UID --gid $USER_GID -m $USERNAME; \
    fi \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME \
    && rm -rf /var/lib/apt/lists/*

USER $USERNAME

WORKDIR /workspace
