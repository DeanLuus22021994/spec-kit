# Dockerfiles Directory

This directory contains all production-optimized Dockerfiles for the Semantic Kernel Application.

## Optimization Standards

All Dockerfiles in this project follow standardized optimization patterns to ensure:

- **Lightweight**: Multi-stage builds with Alpine Linux (~50-150MB final images)
- **Performant**: Named volumes for cache, logs, and data persistence
- **Secure**: Non-root users (UID 1001) across all services
- **Observable**: Health checks with 30-second intervals

See detailed optimization documentation at the end of this file.

## Application Services

### Frontend & Gateway

- **frontend.Dockerfile** - React/TypeScript SPA (Node 20 Alpine)

  - User: `nginx-user:1001`
  - Volumes: `/var/log/nginx`, `/var/cache/nginx`
  - Health check: `wget http://localhost:3000`
  - Final size: ~50MB

- **gateway.Dockerfile** - API Gateway with authentication (.NET 8 Alpine)

  - User: `appuser:1001`
  - Volumes: `/app/logs`, `/app/cache`
  - Health check: `wget http://localhost:80/health`
  - Final size: ~120MB

- **nginx.Dockerfile** - Reverse proxy and load balancer (Nginx Alpine)
  - User: `nginx-user:1001`
  - Custom nginx.conf for non-root compatibility
  - Final size: ~25MB

### Backend Services

- **backend.Dockerfile** - ASP.NET Core Web API (.NET 8 Alpine)

  - User: `appuser:1001`
  - Volumes: `/app/logs`, `/app/data`
  - Health check: `wget http://localhost:80/health`
  - Final size: ~120MB

- **business.Dockerfile** - Business logic layer (.NET 8 Alpine)

  - User: `appuser:1001`
  - Volumes: `/app/logs`, `/app/cache`
  - Health check: `dotnet --info`
  - Final size: ~120MB

- **engine.Dockerfile** - Semantic Kernel processing engine (.NET 8 Alpine)
  - User: `appuser:1001`
  - Volumes: `/app/plugins`, `/app/skills`, `/app/cache`, `/app/logs`
  - Health check: `dotnet --info`
  - Final size: ~120MB

## Data & AI Services

### Database & Storage

- **database.Dockerfile** - PostgreSQL 16 with stored procedures (Alpine)

  - Pre-configured with initialization scripts
  - Health check: `pg_isready`

- **vector.Dockerfile** - Qdrant vector database for semantic search

  - Volumes: `/qdrant/storage`, `/qdrant/snapshots`
  - Health check: `wget http://localhost:6333/healthz`

- **embeddings.Dockerfile** - FastAPI embedding service (Python 3.14 Alpine)
  - User: `appuser:1001`
  - Volumes: `/app/cache`, `/app/logs`, `/app/models`
  - Health check: `wget http://localhost:8001/health`
  - Final size: ~150MB

## Infrastructure Services

### Validation & Quality

- **validation.Dockerfile** - YAML validation service with Kantra CLI

  - User: `toolsuser:1001`
  - Volumes: `/workspace/.config/validation/reports`
  - Kantra CLI from `quay.io/konveyor/kantra:latest`
  - Podman support for hybrid mode
  - Health check: `kantra --version`
  - Final size: ~180MB
  - See: [validation.README.md](./validation.README.md)

### Documentation & DevOps

- **devsite.Dockerfile** - MkDocs Material documentation site

  - User: `docsuser:1001`
  - Volumes: `/docs/site`, `/docs/.cache`
  - Health check: `wget http://localhost:8000`
  - Final size: ~120MB

- **runner.Dockerfile** - GitHub Actions self-hosted runner (official nano image)

  - Volumes: `/runner/_work`

- **devcontainer.Dockerfile** - VS Code development container with all tools

  - Includes dotnet, node, python, git, docker CLI

- **github-mcp.Dockerfile** - GitHub MCP Server (Model Context Protocol)
  - User: `mcp:1001`
  - Volumes: `/app/.cache`, `/app/.git-cache`, `/app/data`
  - Health check: `node --version`
  - Final size: ~150MB

## Volume Strategy

All services use named volumes for data persistence:

```yaml
volumes:
  backend-logs: # Backend service logs
  backend-data: # Backend application data
  engine-plugins: # Semantic Kernel plugins
  engine-skills: # Semantic Kernel skills
  engine-cache: # Engine processing cache
  engine-logs: # Engine service logs
  business-logs: # Business layer logs
  business-cache: # Business layer cache
  gateway-logs: # Gateway service logs
  gateway-cache: # Gateway request cache
  frontend-logs: # Nginx access/error logs
  frontend-cache: # Nginx cache
  embeddings-cache: # Embeddings API cache
  embeddings-logs: # Embeddings service logs
  embeddings-models: # ML model storage
  devsite-site: # Built documentation
  devsite-cache: # MkDocs build cache
  mcp-github-cache: # GitHub MCP cache
  mcp-github-git: # GitHub MCP git cache
  mcp-github-data: # GitHub MCP data
  validation-reports: # YAML validation reports
```

## Usage

Build individual services:

```bash
docker build -f dockerfiles/backend.Dockerfile -t semantic-kernel-backend .
docker build -f dockerfiles/validation.Dockerfile -t semantic-kernel-validation .
```

Build specific docker-compose services:

```bash
# Build all main services
docker-compose build --parallel

# Build validation service
docker-compose -f docker-compose.validation.yml build
```

Run validation service:

```bash
# Using docker-compose
docker-compose -f docker-compose.validation.yml run --rm validation

# Using Makefile
make validate-yaml-docker
```

Validate configuration:

```bash
docker-compose config --quiet
```

Start all services with health monitoring:

```bash
docker-compose up -d
docker ps  # Check health status
```

## Standardized Dockerfile Pattern

All Dockerfiles follow this template:

```dockerfile
# Multi-stage build
FROM base-image:tag-alpine AS build
WORKDIR /app
COPY . .
RUN <build-commands>

FROM runtime-image:tag-alpine AS runtime

# Create non-root user (UID 1001)
RUN addgroup -g 1001 -S appuser && \
    adduser -S appuser -u 1001 -G appuser

# Create volume directories with proper ownership
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appuser /app

# Copy built artifacts
COPY --from=build --chown=appuser:appuser /app/publish .

# Switch to non-root user
USER appuser

# Volume mount points
VOLUME ["/app/logs", "/app/data"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD <health-check-command> || exit 1

EXPOSE <port>
ENTRYPOINT ["<command>"]
```

## Security Features

1. **Non-Root Execution**: All services run as UID 1001 users
2. **Minimal Base Images**: Alpine Linux reduces attack surface
3. **Multi-Stage Builds**: Build tools not included in final images
4. **Health Monitoring**: Automated detection of unhealthy containers
5. **Resource Limits**: CPU and memory constraints in docker-compose.yml

## Performance Optimizations

1. **Persistent Volumes**: Reduce rebuild times by preserving cache and data
2. **Layer Caching**: Optimized COPY order for maximum layer reuse
3. **Parallel Builds**: docker-compose build --parallel for faster builds
4. **Alpine Base**: ~60-70% smaller than standard images
5. **Multi-Stage**: Eliminate build dependencies from runtime

## Image Size Comparison

| Service    | Standard Image | Optimized Alpine | Reduction |
| ---------- | -------------- | ---------------- | --------- |
| Frontend   | ~170MB         | ~50MB            | 70%       |
| Backend    | ~300MB         | ~120MB           | 60%       |
| Engine     | ~300MB         | ~120MB           | 60%       |
| Gateway    | ~300MB         | ~120MB           | 60%       |
| Business   | ~300MB         | ~120MB           | 60%       |
| Embeddings | ~420MB         | ~150MB           | 65%       |
| DevSite    | ~340MB         | ~120MB           | 65%       |
| GitHub MCP | ~500MB         | ~150MB           | 70%       |

## Resource Allocation

Default resource limits in docker-compose.yml:

| Service    | CPU Limit | Memory Limit | Purpose             |
| ---------- | --------- | ------------ | ------------------- |
| Frontend   | 0.25      | 128MB        | Static file serving |
| Backend    | 1.0       | 512MB        | API processing      |
| Engine     | 2.0       | 1GB          | AI workloads        |
| Gateway    | 1.0       | 512MB        | Reverse proxy       |
| Business   | 1.0       | 512MB        | Business logic      |
| Database   | 2.0       | 1GB          | PostgreSQL          |
| Vector     | 1.0       | 512MB        | Qdrant              |
| Embeddings | 1.0       | 512MB        | ML inference        |
| DevSite    | 0.25      | 128MB        | Documentation       |
| Runner     | 2.0       | 2GB          | GitHub Actions      |
| Validation | 1.0       | 1GB          | YAML validation     |

## Maintenance

When updating Dockerfiles:

1. Maintain multi-stage build pattern
2. Keep non-root user (UID 1001)
3. Update health checks if ports change
4. Add volumes for new persistent data
5. Update docker-compose.yml volume mounts
6. Test build: `docker-compose build <service>`
7. Verify health: `docker-compose up -d && docker ps`

## References

- [Docker Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [Docker Health Checks](https://docs.docker.com/engine/reference/builder/#healthcheck)
- [Alpine Linux](https://alpinelinux.org/)
