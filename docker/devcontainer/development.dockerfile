# syntax=docker/dockerfile:1.4
# Final Development Container - Production Ready
FROM spec-kit-tools as development

USER root

# ============================================================================
# PERFORMANCE OPTIMIZATIONS & FINAL SETUP
# ============================================================================
# Final system optimizations
RUN set -eux; \
    # Optimize Python bytecode compilation
    find /usr/local/lib/python3.11 -name "*.py" -exec python3 -m py_compile {} \; || true \
    && find /home/vscode/.local/lib/python3.11 -name "*.py" -exec python3 -m py_compile {} \; 2>/dev/null || true \
    # Set optimal file permissions
    && chmod -R 755 /home/vscode/.cache /home/vscode/.npm /home/vscode/.local 2>/dev/null || true \
    # Clean up any installation artifacts
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# ============================================================================
# HEALTH CHECK & CONTAINER OPTIMIZATION
# ============================================================================
# Health check for container optimization verification
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)" && \
    git --version >/dev/null && \
    docker --version >/dev/null || exit 1

# Switch to non-root user for final image
USER vscode
WORKDIR /workspaces/spec-kit

# Set container entry point
CMD ["/bin/bash", "-c", "sleep infinity"]
