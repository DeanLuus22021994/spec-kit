# Multi-stage build for Documentation Site
# Optimized for minimal size and fast startup with volume persistence

FROM squidfunk/mkdocs-material:9.5.44 AS runtime

WORKDIR /docs

# Create non-root user for security
USER root
RUN addgroup -g 1001 -S docsuser && \
    adduser -S docsuser -u 1001 -G docsuser

# Create directories for persistent volumes
RUN mkdir -p /docs/site /docs/.cache /docs/docs && \
    chown -R docsuser:docsuser /docs

# Copy documentation content to docs subdirectory (excluding mkdocs.yml)
COPY --chown=docsuser:docsuser ./docs/*.md /docs/docs/
COPY --chown=docsuser:docsuser ./docs/*/ /docs/docs/
COPY --chown=docsuser:docsuser ./docs/mkdocs.yml /docs/mkdocs.yml

# Switch to non-root user
USER docsuser

# Volume mount points for persistence
VOLUME ["/docs/site", "/docs/.cache"]

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000 || exit 1

CMD ["serve", "--dev-addr=0.0.0.0:8000"]
