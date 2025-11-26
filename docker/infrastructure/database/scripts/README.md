# Database Scripts

This directory contains utility scripts for database management, backup, restore, and maintenance operations.

## Scripts

### Migration Management

#### `run-migrations.sh`
Executes database migrations in version order.

```bash
# Run all pending migrations
./run-migrations.sh

# Environment variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=semantic_kernel
export DB_USER=user
export MIGRATIONS_DIR=/path/to/migrations
```

**Features:**
- Tracks applied migrations in `schema_migrations` table
- Skips already-applied migrations
- Records execution time and checksums
- Stops on first error
- Shows migration summary

### Seed Data Loading

#### `load-seeds.sh`
Loads seed data for development and testing environments.

```bash
# Load seeds for development
./load-seeds.sh development

# Load seeds for testing
./load-seeds.sh test

# Load seeds for production (not recommended!)
./load-seeds.sh production
```

**Features:**
- Environment-aware loading (blocks production by default)
- Loads all `.sql` files in seeds directory alphabetically
- Shows loading summary and database statistics
- Warns about default passwords

### Backup and Restore

#### `backup.sh`
Creates PostgreSQL database backups with metadata tracking.

```bash
# Create a backup with auto-generated name
./backup.sh

# Create a named backup
./backup.sh my_backup_20240115

# Create a specific backup type
./backup.sh my_backup full       # Full backup
./backup.sh my_backup incremental # Incremental backup
./backup.sh my_backup differential # Differential backup
```

**Environment Variables:**
```bash
export DB_HOST=database
export DB_PORT=5432
export DB_NAME=semantic_kernel
export DB_USER=user
export BACKUP_DIR=/backups
export COMPRESSION=gzip  # or 'none'
```

**Features:**
- Automatic compression (gzip)
- Metadata tracking in `backup_metadata` table
- Checksum calculation for integrity
- File size and duration tracking
- Shows recent backups

#### `restore.sh`
Restores database from backup files.

```bash
# Restore from backup file
./restore.sh /backups/backup_20240115.sql.gz

# Restore with specific type
./restore.sh /path/to/backup.sql full
```

**Features:**
- Safety confirmation prompt
- Automatic decompression detection
- Metadata tracking in `restore_history` table
- Row count verification
- Post-restore statistics

**⚠️ WARNING:** Restore operations OVERWRITE existing data!

## Docker Container Usage

### Run migrations on container startup

```bash
docker-compose exec database /scripts/run-migrations.sh
```

### Create a backup

```bash
docker-compose exec database /scripts/backup.sh backup_$(date +%Y%m%d)
```

### Load seed data

```bash
docker-compose exec database /scripts/load-seeds.sh development
```

## Automation

### Scheduled Backups

Add to crontab for automated backups:

```cron
# Daily backup at 2 AM
0 2 * * * /path/to/backup.sh backup_daily_$(date +%Y%m%d)

# Weekly backup on Sunday at 3 AM
0 3 * * 0 /path/to/backup.sh backup_weekly_$(date +%Y%m%d)
```

### Cleanup Old Backups

```bash
# Remove backups older than 30 days
docker-compose exec database psql -U user -d semantic_kernel -c \
  "SELECT * FROM cleanup_old_backups(30);"
```

### Cleanup Expired Sessions

```bash
# Remove expired sessions
docker-compose exec database psql -U user -d semantic_kernel -c \
  "SELECT cleanup_expired_sessions();"
```

## File Permissions

Scripts need execute permissions:

```bash
chmod +x scripts/*.sh
```

## Troubleshooting

### Permission Denied

```bash
# Grant execute permissions
chmod +x /path/to/script.sh

# Or run with bash explicitly
bash /path/to/script.sh
```

### Database Connection Failed

```bash
# Check environment variables
echo $DB_HOST $DB_PORT $DB_NAME $DB_USER

# Test connection manually
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;"
```

### Migration Failed

```bash
# Check migration status
psql -U user -d semantic_kernel -c \
  "SELECT * FROM schema_migrations ORDER BY version DESC;"

# Manually mark migration as applied (use with caution!)
psql -U user -d semantic_kernel -c \
  "INSERT INTO schema_migrations (version, description) VALUES ('XXX', 'description');"
```

## Best Practices

1. **Always backup before migrations or restores**
   ```bash
   ./backup.sh pre_migration_$(date +%Y%m%d_%H%M%S)
   ./run-migrations.sh
   ```

2. **Test migrations on non-production first**
   - Test on development database
   - Verify in staging environment
   - Then apply to production

3. **Keep backup retention policy**
   - Daily backups: Keep 7 days
   - Weekly backups: Keep 4 weeks
   - Monthly backups: Keep 12 months

4. **Monitor backup size and duration**
   ```bash
   psql -U user -d semantic_kernel -c \
     "SELECT * FROM v_backup_overview ORDER BY created_at DESC LIMIT 10;"
   ```

5. **Never load seed data in production**
   - Contains default passwords
   - Intended for development/testing only
   - Use data imports or manual entry for production

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Run Database Migrations
  run: |
    docker-compose exec -T database /scripts/run-migrations.sh

- name: Load Test Seed Data
  run: |
    docker-compose exec -T database /scripts/load-seeds.sh test
```

### Kubernetes Example

```yaml
initContainers:
  - name: run-migrations
    image: postgres:16-alpine
    command: ["/scripts/run-migrations.sh"]
    volumeMounts:
      - name: scripts
        mountPath: /scripts
      - name: migrations
        mountPath: /migrations
```
