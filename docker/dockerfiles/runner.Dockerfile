# GitHub Actions self-hosted runner using nano image
FROM ghcr.io/actions/actions-runner:2.321.0

# Standard Build Arguments
ARG VERSION=latest
ARG BUILD_DATE
ARG BUILDKIT_INLINE_CACHE=1
ARG DOCKER_BUILDKIT=1

# OCI Labels
LABEL org.opencontainers.image.title="spec-kit-runner"
LABEL org.opencontainers.image.description="GitHub Actions Self-Hosted Runner"
LABEL org.opencontainers.image.source="https://github.com/github/spec-kit"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.vendor="GitHub"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL cache.version="1.0"
LABEL performance.optimized="true"

USER root

# Install minimal dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    jq \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
cd /home/runner\n\
if [ ! -f "/home/runner/.runner" ]; then\n\
  echo "Configuring runner..."\n\
  ./config.sh --url "${REPO_URL}" --token "${RUNNER_TOKEN}" --name "${RUNNER_NAME:-self-hosted-runner}" --work "${RUNNER_WORKDIR:-/runner/_work}" --labels "self-hosted,linux,x64" --unattended --replace\n\
else\n\
  echo "Runner already configured, starting..."\n\
fi\n\
exec ./run.sh' > /home/runner/start.sh \
    && chmod +x /home/runner/start.sh

WORKDIR /home/runner

USER runner

# Health check to verify runner process is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD pgrep -f "Runner.Listener" > /dev/null || exit 1

ENTRYPOINT ["/home/runner/start.sh"]
