# Base Python devcontainer (non-root "vscode" user included)
FROM mcr.microsoft.com/devcontainers/python:3.11

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=1000

# Minimal OS deps and quality-of-life packages
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y --no-install-recommends \
       git curl ca-certificates bash-completion unzip zip \
    && rm -rf /var/lib/apt/lists/*

# Devcontainer scripts
USER root
RUN mkdir -p /opt/devcontainer/scripts
COPY .devcontainer/scripts /opt/devcontainer/scripts
RUN chmod -R +x /opt/devcontainer/scripts

# Install uv once at build time (idempotent)
RUN /opt/devcontainer/scripts/install_uv.sh

# Ensure user exists (provided by base image, but keep DRY)
RUN if ! id -u ${USERNAME} >/dev/null 2>&1; then \
      groupadd --gid ${USER_GID} ${USERNAME} && \
      useradd -s /bin/bash --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME}; \
    fi

# Ownership of caches and scripts
RUN mkdir -p /home/${USERNAME}/.cache/uv /home/${USERNAME}/.cache/pip \
    && chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}/.cache /opt/devcontainer

USER ${USERNAME}
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"
WORKDIR /workspaces/spec-kit