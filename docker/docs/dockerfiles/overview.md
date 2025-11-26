#

# Tools Container (Python 3.14)

## Tools Dockerfile

**File**: `tools/.config/docker/Dockerfile`
**Base**: `python:3.14-slim`
**Purpose**: Provides isolated environment for CLI tools, documentation generation, and code quality checks

### Key Features

- Python 3.14.0 (strict, no backward compatibility)
- All tools baked into the image for instant availability (pip, pre-commit, black, isort, ruff, sqlfluff, Kantra CLI, etc.)
- Non-root user for security
- Named volume persistence for cache and validation data (no host mount)
- Latest package versions always installed

### Named Volumes

Persistent directories are mapped to Docker named volumes for isolation and durability:

- `/app/tools/.mypy_cache` → `tools-mypy-cache`
- `/app/tools/.pytest_cache` → `tools-pytest-cache`
- `/app/tools/.config/validation/reports` → `tools-validation-reports`
- `/app/tools/.config/validation/test-data` → `tools-validation-test-data`

### Example Compose Service

```yaml
services:
  tools:
    build:
      context: ./tools
      dockerfile: .config/docker/Dockerfile
    image: semantic-kernel-tools:latest
    container_name: semantic-kernel-tools
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - tools-mypy-cache:/app/tools/.mypy_cache
      - tools-pytest-cache:/app/tools/.pytest_cache
      - tools-validation-reports:/app/tools/.config/validation/reports
      - tools-validation-test-data:/app/tools/.config/validation/test-data
    networks:
      - app-network
    restart: unless-stopped
```

### Build and Usage

- Build: `docker-compose build tools`
- Run: `docker-compose up tools`
- All tools are instantly available inside the container.

---

---

title: Dockerfile Documentation
description: Reference for all centralized Dockerfiles in the project

---

# Dockerfile Overview

All Dockerfiles are centralized in the `dockerfiles/` directory for consistency and maintainability. Each uses Alpine Linux base images for minimal footprint.

## Directory Structure

```
dockerfiles/
├── backend.Dockerfile      # .NET 10 Web API
├── business.Dockerfile     # Business logic layer
├── database.Dockerfile     # PostgreSQL 16 with stored procedures
├── devcontainer.Dockerfile # Development container
├── devsite.Dockerfile      # MkDocs documentation site
├── embeddings.Dockerfile   # FastAPI embedding service
├── engine.Dockerfile       # Semantic Kernel service
├── frontend.Dockerfile     # React + TypeScript SPA
├── gateway.Dockerfile      # API Gateway with auth
├── nginx.Dockerfile        # Reverse proxy
├── runner.Dockerfile       # GitHub Actions self-hosted runner
├── vector.Dockerfile       # Qdrant vector database
└── README.md              # Dockerfile documentation
```

## Design Principles

### 🏔️ Alpine Linux Base

All images use Alpine Linux for minimal size:

- .NET 10 Alpine: ~256MB base
- Node 20 Alpine: ~180MB base
- Python 3.14 Alpine: ~120MB base

### 🎯 Multi-Stage Builds

Separate build and runtime stages to minimize final image size.

### 🔒 Non-Root Users

All containers run as non-root users for security.

### 📦 Dependency Caching

Strategic layer ordering to maximize Docker cache effectiveness.

---

## Dockerfile Details

### Backend Dockerfile

**File**: `dockerfiles/backend.Dockerfile`
**Base**: `mcr.microsoft.com/dotnet/aspnet:10.0-alpine`
**Purpose**: ASP.NET Core Web API with REST endpoints

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:10.0-alpine AS build
WORKDIR /src
COPY src/backend/backend.csproj .
RUN dotnet restore
COPY src/backend/ .
RUN dotnet publish -c Release -o /app

FROM mcr.microsoft.com/dotnet/aspnet:10.0-alpine
WORKDIR /app
COPY --from=build /app .
USER appuser
ENTRYPOINT ["dotnet", "backend.dll"]
```

**Features**:

- Multi-stage build
- Dependency layer caching
- Non-root user
- Release configuration

---

### Engine Dockerfile

**File**: `dockerfiles/engine.Dockerfile`
**Base**: `mcr.microsoft.com/dotnet/aspnet:10.0-alpine`
**Purpose**: Semantic Kernel AI processing service

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:10.0-alpine AS build
WORKDIR /src
COPY src/engine/engine.csproj .
RUN dotnet restore
COPY src/engine/ .
RUN dotnet publish -c Release -o /app

FROM mcr.microsoft.com/dotnet/aspnet:10.0-alpine
WORKDIR /app
COPY --from=build /app .
COPY .config/semantic-kernel.yml /app/config/
USER appuser
ENTRYPOINT ["dotnet", "engine.dll"]
```

**Features**:

- Includes kernel configuration
- Optimized for AI workloads
- Semantic Kernel SDK

---

### Frontend Dockerfile

**File**: `dockerfiles/frontend.Dockerfile`
**Base**: `node:20-alpine`
**Purpose**: React + TypeScript SPA with Vite

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY src/frontend/package*.json ./
RUN npm ci
COPY src/frontend/ .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=build /app/dist ./dist
USER node
CMD ["serve", "-s", "dist", "-l", "3000"]
```

**Features**:

- Production build with Vite
- Static file serving
- Minimal runtime dependencies

---

### Database Dockerfile

**File**: `dockerfiles/database.Dockerfile`
**Base**: `postgres:16-alpine`
**Purpose**: PostgreSQL with stored procedures and optimizations

```dockerfile
FROM postgres:16-alpine

# Install additional tools
RUN apk add --no-cache curl

# Copy initialization scripts
COPY infrastructure/database/init.sql /docker-entrypoint-initdb.d/

# PostgreSQL optimizations
ENV POSTGRES_INITDB_ARGS="--encoding=UTF8 --locale=C"
ENV POSTGRES_HOST_AUTH_METHOD=md5

# Performance tuning
RUN echo "shared_buffers = 128MB" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "effective_cache_size = 512MB" >> /usr/local/share/postgresql/postgresql.conf.sample
```

**Features**:

- Stored procedures for auth
- Performance tuning
- UTF-8 encoding

---

### Vector Dockerfile

**File**: `dockerfiles/vector.Dockerfile`
**Base**: `qdrant/qdrant:v1.7.4`
**Purpose**: Qdrant vector database for semantic search

```dockerfile
FROM qdrant/qdrant:v1.7.4

# Copy Qdrant configuration
COPY semantic/vector/config.yml /qdrant/config/production.yaml

# Create data directory
RUN mkdir -p /qdrant/storage

EXPOSE 6333 6334

CMD ["./qdrant", "--config-path", "/qdrant/config/production.yaml"]
```

**Features**:

- 1536-dimensional vectors
- HNSW indexing
- gRPC and HTTP APIs

---

### Embeddings Dockerfile

**File**: `dockerfiles/embeddings.Dockerfile`
**Base**: `python:3.14-alpine`
**Purpose**: FastAPI service for generating embeddings

```dockerfile
FROM python:3.14-alpine AS build

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev

# Install Python dependencies
COPY tools/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-alpine

WORKDIR /app

# Copy installed packages
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY tools/*.py .
COPY semantic/embeddings/config.yml /app/config/

EXPOSE 8001

CMD ["uvicorn", "embeddings:app", "--host", "0.0.0.0", "--port", "8001"]
```

**Features**:

- FastAPI framework
- OpenAI integration
- PostgreSQL caching

---

### Gateway Dockerfile

**File**: `dockerfiles/gateway.Dockerfile`
**Base**: `mcr.microsoft.com/dotnet/aspnet:10.0-alpine`
**Purpose**: API Gateway with authentication and routing

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:10.0-alpine AS build
WORKDIR /src
COPY src/gateway/gateway.csproj .
RUN dotnet restore
COPY src/gateway/ .
RUN dotnet publish -c Release -o /app

FROM mcr.microsoft.com/dotnet/aspnet:10.0-alpine
WORKDIR /app
COPY --from=build /app .
USER appuser
EXPOSE 8080
ENTRYPOINT ["dotnet", "gateway.dll"]
```

**Features**:

- JWT authentication
- Reverse proxy
- Rate limiting

---

### DevSite Dockerfile

**File**: `dockerfiles/devsite.Dockerfile`
**Base**: `python:3.11-alpine`
**Purpose**: MkDocs Material documentation site

```dockerfile
FROM python:3.11-alpine

WORKDIR /docs

RUN pip install --no-cache-dir \
    mkdocs-material \
    mkdocs-minify-plugin \
    mkdocs-git-revision-date-localized-plugin \
    mkdocs-git-committers-plugin-2 \
    mkdocs-awesome-pages-plugin \
    mkdocs-macros-plugin \
    mkdocs-glightbox

COPY docs/ .

EXPOSE 8000

CMD ["mkdocs", "serve", "--dev-addr=0.0.0.0:8000"]
```

**Features**:

- Material theme
- Search functionality
- Live reload

---

### Runner Dockerfile

**File**: `dockerfiles/runner.Dockerfile`
**Base**: `ghcr.io/actions/actions-runner:latest`
**Purpose**: GitHub Actions self-hosted runner

```dockerfile
FROM ghcr.io/actions/actions-runner:latest

USER root

# Install additional tools
RUN apt-get update && apt-get install -y \
    curl \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

USER runner

WORKDIR /home/runner
```

**Features**:

- Official GitHub runner image
- Minimal additional tools
- Non-root execution

---

## Build Commands

### Build All Images

```bash
docker-compose build
```

### Build Specific Service

```bash
docker-compose build backend
docker-compose build engine
docker-compose build frontend
```

### Build with No Cache

```bash
docker-compose build --no-cache
```

---

## Image Sizes

| Service    | Image Size | Base Image           |
| ---------- | ---------- | -------------------- |
| Backend    | ~280MB     | .NET 10 Alpine       |
| Engine     | ~290MB     | .NET 10 Alpine       |
| Business   | ~270MB     | .NET 10 Alpine       |
| Frontend   | ~200MB     | Node 20 Alpine       |
| Gateway    | ~275MB     | .NET 10 Alpine       |
| Database   | ~240MB     | PostgreSQL 16 Alpine |
| Vector     | ~180MB     | Qdrant Official      |
| Embeddings | ~250MB     | Python 3.14 Alpine   |
| Nginx      | ~40MB      | Nginx Alpine         |
| DevSite    | ~180MB     | Python 3.14 Alpine   |

**Total**: ~2.2GB for all services

---

## Best Practices

1. **Layer Ordering**: Place frequently changing files last
2. **Cache Dependencies**: Install dependencies before copying source
3. **Multi-Stage Builds**: Separate build and runtime environments
4. **Security**: Run as non-root user
5. **Health Checks**: Include HEALTHCHECK instructions
6. **Labels**: Add metadata labels for tracking

---

## Related Documentation

- [Docker Compose Configuration](../configuration/docker-compose.md)
- [Service Architecture](../architecture/services.md)
- [Development Setup](../development/setup.md)
