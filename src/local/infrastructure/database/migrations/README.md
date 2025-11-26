# Database Migrations

This directory contains versioned database migration scripts for the Semantic Kernel application.

## Naming Convention

Migration files follow the pattern: `V{version}__{description}.sql`

- `V` prefix indicates a versioned migration
- `{version}` is a numeric version (e.g., 001, 002, 003)
- `__` double underscore separator
- `{description}` snake_case description of the migration

## Migration Order

Migrations are executed in version order:

1. **V001\_\_schema_version_table.sql** - Create migration tracking table
2. **V002\_\_pgvector_extension.sql** - Install pgvector extension for embeddings
3. **V003\_\_conversation_indexes.sql** - Add performance indexes for conversations
4. **V004\_\_api_rate_limiting.sql** - Add rate limiting tables
5. **V005\_\_backup_restore_procedures.sql** - Add backup/restore stored procedures

## How to Add a New Migration

1. Create a new SQL file following the naming convention
2. Increment the version number from the last migration
3. Add your DDL statements (CREATE, ALTER, DROP, etc.)
4. Test locally before committing
5. Migrations are executed automatically on container startup

## Rollback Strategy

- Migrations are one-way (forward only)
- To rollback, create a new migration that reverses changes
- Keep backups before running migrations in production

## Testing Migrations

```bash
# Test migration locally
docker-compose exec database psql -U user -d semantic_kernel -f /migrations/V00X__description.sql

# Check migration status
docker-compose exec database psql -U user -d semantic_kernel -c "SELECT * FROM schema_migrations ORDER BY version;"
```

## Best Practices

- ✓ Make migrations idempotent (use `IF NOT EXISTS`, `IF EXISTS`)
- ✓ Test migrations on a copy of production data
- ✓ Keep migrations small and focused
- ✓ Document complex migrations
- ✓ Always backup before running migrations
- ✗ Never modify existing migration files after they're applied
- ✗ Don't include seed data in migrations (use seeds/ directory)
