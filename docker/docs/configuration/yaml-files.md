---
title: YAML Configuration Files
description: Reference documentation for all YAML configuration files in the project
---

# YAML Configuration Files

All YAML configuration files are centralized in the `.config/` directory for easy management and version control.

## CLI Configuration

**File**: `.config/cli.yml`

Command-line interface configuration for the Python CLI tool located in `tools/cli.py`.

### Purpose

Defines CLI commands, API endpoints, database connections, OpenAI settings, and feature flags for the semantic kernel CLI operations.

### Key Sections

#### CLI Settings

```yaml
cli:
  name: "sk-cli"
  description: "Semantic Kernel CLI for managing AI operations"
  version: "1.0.0"
  default_output: "json"
  verbose: false
```

#### Commands

Defines available commands and subcommands:

- `kernel`: create, list, delete, status
- `plugins`: install, list, remove, update
- `skills`: add, list, invoke, test
- `embeddings`: generate, search, index, query
- `config`: show, set, reset

#### API Endpoints

```yaml
api:
  base_url: "http://localhost:5000"
  timeout: 30
  retry_attempts: 3
  endpoints:
    backend: "http://localhost:5000"
    engine: "http://localhost:5001"
    embeddings: "http://localhost:8001"
    vector: "http://localhost:6333"
```

#### Database Configuration

PostgreSQL connection settings with environment variable for password.

#### Vector Database

Qdrant configuration for semantic search operations.

#### OpenAI Configuration

Settings for GPT-4 and text-embedding-3-small models.

---

## Semantic Kernel Configuration

**File**: `.config/semantic-kernel.yml`

Core configuration for the Semantic Kernel AI engine.

### Purpose

Defines kernel settings, plugin directories, planner configurations, and memory store settings.

### Key Sections

#### Kernel Settings

- Plugins path: `/app/plugins`
- Skills path: `/app/skills`
- Memory store: PostgreSQL
- Planner: SequentialPlanner
- Max iterations: 10

#### Planners

- Sequential Planner
- Action Planner
- Stepwise Planner

---

## Services Configuration

**File**: `.config/services.yml`

Resource allocation and limits for all Docker services.

### Purpose

Defines CPU and memory limits for each microservice to optimize resource usage.

### Resource Allocation

| Service      | CPUs | Memory | Notes          |
| ------------ | ---- | ------ | -------------- |
| Frontend     | 0.5  | 256MB  | React SPA      |
| Backend      | 1.0  | 512MB  | API Server     |
| Engine       | 2.0  | 1GB    | AI Processing  |
| Business     | 0.5  | 512MB  | Logic Layer    |
| Gateway      | 0.5  | 256MB  | Auth & Routing |
| Database     | 1.0  | 512MB  | PostgreSQL     |
| Vector       | 2.0  | 1GB    | Qdrant         |
| Embeddings   | 2.0  | 2GB    | FastAPI        |
| Nginx        | 0.25 | 128MB  | Reverse Proxy  |
| DevSite      | 0.25 | 128MB  | MkDocs         |
| Runner       | 2.0  | 2GB    | GitHub Actions |
| Redis        | 0.5  | 256MB  | Cache          |
| RedisInsight | 0.25 | 256MB  | Redis UI       |

**Total**: ~13.75 CPUs, ~9.25GB RAM

---

## Infrastructure Configuration

**File**: `.config/infrastructure.yml`

Network, logging, and monitoring settings for the entire infrastructure.

### Purpose

Centralized configuration for:

- Docker network settings
- Logging levels and formats
- Health check intervals
- Monitoring endpoints

### Key Settings

#### Network

- Subnet: 172.20.0.0/16
- Gateway: 172.20.0.1
- Driver: bridge

#### Logging

- Default level: info
- Format: JSON
- Max size: 10MB
- Max files: 3

#### Health Checks

- Interval: 30s
- Timeout: 10s
- Retries: 3
- Start period: 40s

---

## Vector Database Configuration

**File**: `semantic/vector/config.yml`

Qdrant vector database configuration for semantic search.

### Purpose

Configures the Qdrant instance for storing and searching 1536-dimensional embeddings.

### Key Settings

```yaml
qdrant:
  host: "vector"
  port: 6333
  grpc_port: 6334
  collection: "embeddings"
  vector_size: 1536
  distance: "Cosine"
  on_disk_payload: true
  hnsw_config:
    m: 16
    ef_construct: 100
  quantization:
    type: "scalar"
```

### Features

- HNSW indexing for fast approximate search
- Scalar quantization for reduced memory usage
- On-disk payload storage
- Cosine distance for similarity

---

## Embeddings Configuration

**File**: `semantic/embeddings/config.yml`

FastAPI embeddings service configuration.

### Purpose

Configures the Python-based embedding generation service using OpenAI's text-embedding-3-small model.

### Key Settings

```yaml
embeddings:
  model: "text-embedding-3-small"
  dimensions: 1536
  batch_size: 100
  timeout: 60
  cache:
    enabled: true
    backend: "postgresql"
    ttl: 86400 # 24 hours
```

### Features

- Batch processing for efficiency
- PostgreSQL caching with 24-hour TTL
- OpenAI API integration
- FastAPI server on port 8001

---

## Usage Examples

### CLI Tool Usage

```bash
# Show configuration
python tools/cli.py --show-config

# List available commands
python tools/cli.py --list-commands

# Use custom config file
python tools/cli.py --config /path/to/config.yml
```

### Environment Variables

Required environment variables referenced in configs:

```bash
# Database
DB_PASSWORD=your_password

# OpenAI
OPENAI_API_KEY=sk-...

# Authentication
SK_API_TOKEN=your_token
```

---

## Best Practices

1. **Version Control**: Keep all YAML files in version control
2. **Secrets**: Use environment variables for sensitive data
3. **Validation**: Validate YAML syntax before deployment
4. **Documentation**: Update docs when changing configurations
5. **Backups**: Maintain backups of production configurations

---

## Related Files

- [Docker Compose Configuration](docker-compose.md)
- [Environment Variables](environment.md)
- [Python CLI Documentation](../cli/python-cli.md)
