# Infrastructure

This directory contains all infrastructure configuration and resources for the Semantic Kernel Application, including database schemas, reverse proxy configuration, caching, and CI/CD runner setup.

## Overview

```
infrastructure/
├── database/         # PostgreSQL configuration and migrations
├── nginx/           # Reverse proxy configuration
├── redis/           # Cache configuration
└── runner/          # GitHub Actions self-hosted runner
```

## Components

### Database (PostgreSQL 16)

The database infrastructure provides:

- PostgreSQL 16 with pgvector extension
- Versioned migrations
- Seed data for development/testing
- Backup and restore scripts

**Key Features:**

- Vector similarity search for semantic embeddings
- Full-text search on message content
- Built-in rate limiting
- Audit logging

📖 [Database Documentation](database/README.md)

### Nginx (Reverse Proxy)

Nginx serves as the public entry point:

- Request routing to backend services
- SSL/TLS termination
- Load balancing
- Static file serving

**Configuration:** `nginx/nginx.conf`

### Redis (Cache)

Redis provides:

- Session storage
- Response caching
- Rate limit counters
- Pub/sub for real-time features

**Configuration:** `redis/redis.conf`

### GitHub Actions Runner

Self-hosted runner for CI/CD:

- Uses GitHub's official nano image
- Auto-registration with repository
- Minimal footprint (2 CPU, 2GB RAM)

**Configuration:** `runner/config`

## Network Architecture

All infrastructure components communicate through an isolated Docker network:

```
┌─────────────────────────────────────────────────────────────┐
│                    app-network (172.20.0.0/16)              │
│                                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │  Nginx  │───▶│ Gateway │───▶│ Backend │───▶│ Engine  │  │
│  │  :80    │    │  :8080  │    │  :5000  │    │         │  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘  │
│                      │              │              │        │
│                      │              ▼              ▼        │
│                      │         ┌─────────┐   ┌─────────┐   │
│                      └────────▶│  Redis  │   │ Database│   │
│                                │  :6379  │   │  :5432  │   │
│                                └─────────┘   └─────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Resource Allocation

| Service  | CPU Limit | Memory Limit |
| -------- | --------- | ------------ |
| Database | 1.0       | 512MB        |
| Redis    | 0.5       | 256MB        |
| Nginx    | 0.25      | 128MB        |
| Runner   | 2.0       | 2GB          |

## Quick Start

### Start All Infrastructure

```bash
# Start all services including infrastructure
docker-compose up -d

# Start only infrastructure services
docker-compose up -d database redis nginx
```

### Database Setup

```bash
# Migrations run automatically on first start
# To manually run migrations:
docker-compose exec database /scripts/run-migrations.sh

# Load seed data (development only)
docker-compose exec database /scripts/load-seeds.sh development
```

### Redis Configuration

```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# Check memory usage
docker-compose exec redis redis-cli info memory
```

### Nginx Reload

```bash
# Reload nginx configuration
docker-compose exec nginx nginx -s reload

# Test configuration
docker-compose exec nginx nginx -t
```

## Environment Variables

### Database

| Variable            | Description       | Default           |
| ------------------- | ----------------- | ----------------- |
| `POSTGRES_DB`       | Database name     | `semantic_kernel` |
| `POSTGRES_USER`     | Database user     | `user`            |
| `POSTGRES_PASSWORD` | Database password | Required          |
| `DATABASE_SEED_ENV` | Seed environment  | `development`     |

### Redis

| Variable          | Description    | Default  |
| ----------------- | -------------- | -------- |
| `REDIS_PASSWORD`  | Redis password | Optional |
| `REDIS_MAXMEMORY` | Max memory     | `256mb`  |

### Runner

| Variable              | Description        | Required |
| --------------------- | ------------------ | -------- |
| `GITHUB_RUNNER_TOKEN` | Registration token | Yes      |
| `GITHUB_REPO_URL`     | Repository URL     | Yes      |

## Security Considerations

### Production Deployment

1. **Database Security**

   - Change default passwords
   - Enable SSL connections
   - Restrict network access

2. **Redis Security**

   - Enable authentication
   - Bind to internal network only

3. **Nginx Security**
   - Enable HTTPS
   - Configure security headers
   - Rate limiting

### Access Control

- Database: Role-based access control (RBAC)
- Redis: ACL support for user permissions
- Nginx: IP-based access control

## Monitoring

### Health Checks

All infrastructure services have health checks:

```bash
# Check service health
docker-compose ps

# View health check logs
docker-compose logs database | grep health
```

### Metrics

- **PostgreSQL**: `pg_stat_statements` extension
- **Redis**: Built-in INFO command
- **Nginx**: Access and error logs

## Backup and Recovery

### Database Backups

```bash
# Create backup
docker-compose exec database /scripts/backup.sh backup_$(date +%Y%m%d)

# Restore backup
docker-compose exec database /scripts/restore.sh /backups/backup_20240115.sql.gz
```

### Redis Persistence

Redis is configured with RDB snapshots:

- Save every 900 seconds if 1 key changed
- Save every 300 seconds if 10 keys changed
- Save every 60 seconds if 10000 keys changed

## Troubleshooting

### Database Issues

```bash
# Check connection
docker-compose exec database pg_isready -U user

# View logs
docker-compose logs database

# Connect directly
docker-compose exec database psql -U user -d semantic_kernel
```

### Redis Issues

```bash
# Check status
docker-compose exec redis redis-cli ping

# View memory
docker-compose exec redis redis-cli info memory

# Clear cache (caution!)
docker-compose exec redis redis-cli flushall
```

### Nginx Issues

```bash
# Test configuration
docker-compose exec nginx nginx -t

# View access logs
docker-compose logs nginx

# Check upstream status
docker-compose exec nginx curl -I http://backend:5000/health
```

## Related Documentation

- [Architecture Overview](../ARCHITECTURE.md)
- [Development Guide](../DEVELOPMENT.md)
- [Database README](database/README.md)
- [Docker Compose Configuration](../docker-compose.yml)
