# Python 3.14.0 SOAP Client Embedding
# PRECOMPILED: All dependencies baked in for 3rd party SOAP API integration
# =====================================================
# Features:
# - Python 3.14.0 with latest syntax (generic typing, pattern matching, etc.)
# - Full SOAP/WSDL client stack (zeep, suds-community)
# - Modern HTTP clients (httpx, requests, aiohttp)
# - XML processing (lxml, defusedxml, xmltodict)
# - Data validation (pydantic)
# - Async support with uvloop
# =====================================================

# Stage 1: Build with all dependencies
FROM python:3.14-slim AS builder

LABEL maintainer="Semantic Kernel App Team"
LABEL description="Python 3.14 SOAP client embedding for 3rd party API integration"
LABEL version="1.0.0"

WORKDIR /app

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  libxml2-dev \
  libxslt1-dev \
  libffi-dev \
  libssl-dev \
  git \
  curl \
  ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Install all SOAP/API dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
  pip install --no-cache-dir \
  "zeep>=4.3.1" \
  "suds-community>=1.2.0" \
  "lxml>=5.3.0" \
  "defusedxml>=0.7.1" \
  "xmltodict>=0.14.2" \
  "pysimplesoap>=1.16.2" \
  "httpx>=0.28.1" \
  "requests>=2.32.3" \
  "aiohttp>=3.11.9" \
  "urllib3>=2.2.3" \
  "certifi>=2024.12.14" \
  "pydantic>=2.10.3" \
  "pydantic-settings>=2.7.0" \
  "orjson>=3.10.12" \
  "python-dateutil>=2.9.0" \
  "uvloop>=0.21.0" \
  "aiocache>=0.12.3" \
  "tenacity>=9.0.0" \
  "cryptography>=44.0.0" \
  "signxml>=4.0.2" \
  "python-jose>=3.3.0" \
  "structlog>=24.4.0" \
  "opentelemetry-api>=1.28.2" \
  "opentelemetry-sdk>=1.28.2" \
  "opentelemetry-instrumentation-httpx>=0.49b2" \
  "opentelemetry-instrumentation-requests>=0.49b2" \
  "click>=8.1.7" \
  "rich>=13.9.4" \
  "python-dotenv>=1.0.1" \
  "pyyaml>=6.0.2" \
  "pytest>=8.3.4" \
  "pytest-asyncio>=0.24.0" \
  "pytest-httpx>=0.35.0" \
  "responses>=0.25.3"

# Stage 2: Runtime image
FROM python:3.14-slim AS runtime

LABEL maintainer="Semantic Kernel App Team"
LABEL description="Python 3.14 SOAP client - production ready"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
  libxml2 \
  libxslt1.1 \
  ca-certificates \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r -g 1001 soapclient && \
  useradd -r -u 1001 -g soapclient -m -s /bin/bash soapclient

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create directories
RUN mkdir -p /app/soap /app/wsdl /app/cache /app/logs /app/examples

# Copy SOAP client source from semantic/soap
COPY --chown=soapclient:soapclient semantic/soap/ /app/soap/

# Set ownership
RUN chown -R soapclient:soapclient /app

# Switch to non-root user
USER soapclient

# Environment variables
ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=/app \
  SOAP_CACHE_PATH=/app/cache \
  SOAP_LOG_LEVEL=INFO

# Volume mounts for persistence
VOLUME ["/app/cache", "/app/logs", "/app/wsdl"]

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import zeep, httpx, lxml, pydantic, structlog, tenacity; print('OK')" || exit 1
