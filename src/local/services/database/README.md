# =====================================================

# Database Infrastructure Documentation

# =====================================================

This directory contains the complete database infrastructure for the Semantic Kernel application, including initialization scripts, migrations, seed data, and management utilities.

## 📁 Directory Structure

```
infrastructure/database/
├── init.sql                    # Initial database schema and setup
├── migrations/                 # Versioned database migrations
│   ├── README.md
│   ├── V001__schema_version_table.sql
│   ├── V002__pgvector_extension.sql
│   ├── V003__conversation_indexes.sql
│   ├── V004__api_rate_limiting.sql
│   └── V005__backup_restore_procedures.sql
├── seeds/                      # Development/test seed data
│   ├── README.md
│   ├── 001_dev_users.sql
│   ├── 002_sample_conversations.sql
│   ├── 003_demo_skills.sql
│   ├── 004_test_embeddings.sql
│   └── 005_api_test_data.sql
└── scripts/                    # Database management scripts
    ├── README.md
    ├── backup.sh
    ├── restore.sh
    ├── run-migrations.sh
    └── load-seeds.sh
```

## 🗄️ Database Schema Overview

### Core Application Tables

- **users** - User accounts with authentication
- **roles** - Role-based access control (RBAC)
- **user_roles** - User-role junction table
- **sessions** - Session management
- **user_quotas** - API rate limiting quotas

### Semantic Kernel Tables

- **conversations** - Chat/conversation sessions
- **messages** - Messages within conversations
- **semantic_memories** - Semantic memory store
- **embeddings** - Vector embeddings (with pgvector)
- **skills** - Registered semantic kernel skills
- **function_executions** - Function execution logs
- **planner_executions** - Planner execution tracking

### Supporting Tables

- **api_usage** - API usage tracking and analytics
- **audit_logs** - Audit trail for compliance
- **rate_limit_tracking** - Rate limiting counters
- **backup_metadata** - Backup tracking
- **restore_history** - Restore operation history
- **schema_migrations** - Migration version tracking

## 🚀 Quick Start

### 1. Initial Setup

The database initializes automatically on first run:

```bash
# Start the database service
docker-compose up database

# Migrations and seeds run automatically based on DATABASE_SEED_ENV
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Database credentials
DATABASE_NAME=semantic_kernel
DATABASE_USER=user
DATABASE_PASSWORD=your_secure_password_here

# Environment (controls seed data loading)
DATABASE_SEED_ENV=development  # development, test, or production
```

### 3. Verify Setup

```bash
# Check migration status
docker-compose exec database psql -U user -d semantic_kernel -c \
  "SELECT version, description, applied_at FROM schema_migrations ORDER BY version;"

# Check database statistics
docker-compose exec database psql -U user -d semantic_kernel -c \
  "SELECT * FROM get_database_statistics();"
```

## 📊 Key Features

### 1. Vector Similarity Search (pgvector)

Support for semantic embeddings with cosine similarity search:

```sql
-- Search similar embeddings
SELECT * FROM search_similar_embeddings(
    query_embedding := '[0.1, 0.2, ...]'::vector(1536),
    p_collection := 'documents',
    p_user_id := 'user-uuid',
    p_limit := 10,
    p_threshold := 0.7
);
```

### 2. Full-Text Search

PostgreSQL full-text search on message content:

```sql
-- Search messages
SELECT * FROM search_messages(
    p_user_id := 'user-uuid',
    p_search_query := 'semantic kernel',
    p_limit := 50
);
```

### 3. Rate Limiting

Built-in API rate limiting with quotas:

```sql
-- Check rate limit
SELECT * FROM check_rate_limit(
    p_user_id := 'user-uuid',
    p_tokens := 100
);

-- Increment counters
SELECT increment_rate_limit(
    p_user_id := 'user-uuid',
    p_tokens := 100
);
```

### 4. Backup & Restore

Automated backup with metadata tracking:

```bash
# Create backup
docker-compose exec database /scripts/backup.sh backup_20240115

# Restore from backup
docker-compose exec database /scripts/restore.sh /backups/backup_20240115.sql.gz
```

## 🔧 Management Commands

### Migrations

```bash
# Run pending migrations
docker-compose exec database /scripts/run-migrations.sh

# Check migration status
docker-compose exec database psql -U user -d semantic_kernel -c \
  "SELECT * FROM schema_migrations ORDER BY version DESC LIMIT 10;"
```

### Seed Data

```bash
# Load development seeds
docker-compose exec database /scripts/load-seeds.sh development

# Load test seeds
docker-compose exec database /scripts/load-seeds.sh test

# ⚠️ Production (not recommended)
docker-compose exec database /scripts/load-seeds.sh production
```

### Backups

```bash
# Create full backup
docker-compose exec database /scripts/backup.sh backup_$(date +%Y%m%d) full

# List recent backups
docker-compose exec database psql -U user -d semantic_kernel -c \
  "SELECT * FROM v_backup_overview ORDER BY created_at DESC LIMIT 10;"

# Cleanup old backups (keep last 30 days)
docker-compose exec database psql -U user -d semantic_kernel -c \
  "SELECT * FROM cleanup_old_backups(30);"
```

### Maintenance

```bash
# Cleanup expired sessions
docker-compose exec database psql -U user -d semantic_kernel -c \
  "SELECT cleanup_expired_sessions();"

# Cleanup old rate limit data
docker-compose exec database psql -U user -d semantic_kernel -c \
  "SELECT cleanup_rate_limit_data();"

# Vacuum and analyze
docker-compose exec database psql -U user -d semantic_kernel -c \
  "VACUUM ANALYZE;"
```

## 🔐 Security Considerations

### Production Deployment

1. **Change Default Passwords**

   ```bash
   # Set in .env file
   DATABASE_PASSWORD=strong_random_password_here
   ```

2. **Disable Seed Data**

   ```bash
   DATABASE_SEED_ENV=production
   ```

3. **Configure Firewall**

   - Restrict database port (5432) to application network only
   - Never expose directly to internet

4. **Enable SSL/TLS**

   ```sql
   -- Configure SSL in PostgreSQL
   ssl = on
   ssl_cert_file = '/path/to/server.crt'
   ssl_key_file = '/path/to/server.key'
   ```

5. **Regular Backups**

   - Schedule automated backups
   - Test restore procedures
   - Store backups securely off-site

6. **Audit Logging**
   - Monitor `audit_logs` table
   - Set up alerts for suspicious activity

### Access Control

Default roles created:

- **admin** - Full system access
- **developer** - Extended development permissions
- **user** - Standard user access
- **readonly** - Read-only access

Seed data users (development only):

- admin / Admin@123 (change immediately!)
- developer / Dev@12345
- testuser / Dev@12345
- readonly / Dev@12345

**⚠️ Change all default passwords before deployment!**

## 📈 Performance Tuning

### Indexes

Key indexes are created by migration V003:

- Conversation queries: `idx_conversations_user_recent`
- Message searches: `idx_messages_content_fts`
- Vector similarity: `idx_embeddings_vector` (IVFFlat)
- JSONB metadata: `idx_conversations_metadata` (GIN)

### Configuration

Optimized for 512MB memory limit:

```ini
shared_buffers = 128MB
effective_cache_size = 256MB
work_mem = 4MB
maintenance_work_mem = 64MB
```

Adjust based on your deployment:

```bash
# For larger deployments (2GB RAM)
shared_buffers = 512MB
effective_cache_size = 1GB
work_mem = 16MB
```

### Monitoring

```sql
-- Slow queries
SELECT * FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

-- Table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index usage
SELECT
    indexrelname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

## 🐛 Troubleshooting

### Migration Failures

```bash
# Check current migration version
docker-compose exec database psql -U user -d semantic_kernel -c \
  "SELECT MAX(version) FROM schema_migrations;"

# Manually mark migration as applied (use with caution!)
docker-compose exec database psql -U user -d semantic_kernel -c \
  "INSERT INTO schema_migrations (version, description)
   VALUES ('005', 'backup_restore_procedures');"
```

### Connection Issues

```bash
# Check if database is running
docker-compose ps database

# Check logs
docker-compose logs database

# Test connection
docker-compose exec database pg_isready -U user -d semantic_kernel
```

### Disk Space

```bash
# Check database size
docker-compose exec database psql -U user -d semantic_kernel -c \
  "SELECT pg_size_pretty(pg_database_size('semantic_kernel'));"

# Cleanup old data
docker-compose exec database psql -U user -d semantic_kernel -c \
  "SELECT cleanup_expired_sessions();
   SELECT cleanup_rate_limit_data();"
```

## 📚 References

- [PostgreSQL Documentation](https://www.postgresql.org/docs/16/)
- [pgvector Extension](https://github.com/pgvector/pgvector)
- [Database Migration Best Practices](https://www.postgresql.org/docs/current/ddl.html)
- [Full-Text Search](https://www.postgresql.org/docs/current/textsearch.html)
- [Docker PostgreSQL](https://hub.docker.com/_/postgres)

## 📝 Change Log

### Version 1.0.0 (2024-01-15)

- ✅ Initial database schema with comprehensive tables
- ✅ Migration system with version tracking
- ✅ Seed data for development/testing
- ✅ Backup and restore procedures
- ✅ pgvector extension for embeddings
- ✅ Full-text search on messages
- ✅ Rate limiting implementation
- ✅ Audit logging
- ✅ Management scripts
- ✅ Environment-aware initialization
- ✅ Automated migration execution
- ✅ Health checks and monitoring

## 🤝 Contributing

When adding new migrations:

1. Create new migration file: `V00X__description.sql`
2. Make migrations idempotent (`IF NOT EXISTS`, etc.)
3. Test on development database
4. Update migration documentation
5. Record in schema_migrations table
6. Add migration to Dockerfile COPY command

## 📞 Support

For issues or questions:

- Check troubleshooting section above
- Review migration logs
- Consult PostgreSQL documentation
- Check Docker logs: `docker-compose logs database`
