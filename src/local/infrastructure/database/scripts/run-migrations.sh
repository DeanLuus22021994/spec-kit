#!/bin/bash
# Database Migration Runner
# Purpose: Execute database migrations in version order
# Usage: ./run-migrations.sh

set -e  # Exit on error

# Configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-semantic_kernel}"
DB_USER="${DB_USER:-user}"
MIGRATIONS_DIR="${MIGRATIONS_DIR:-/migrations}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Database Migration Runner${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Database: $DB_NAME"
echo "Migrations Directory: $MIGRATIONS_DIR"
echo ""

# Check if migrations directory exists
if [ ! -d "$MIGRATIONS_DIR" ]; then
    echo -e "${RED}Error: Migrations directory not found: $MIGRATIONS_DIR${NC}"
    exit 1
fi

# Check database connection
echo -e "${YELLOW}Checking database connection...${NC}"
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}Error: Cannot connect to database${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Database connection successful${NC}"
echo ""

# Get applied migrations
echo -e "${YELLOW}Checking migration status...${NC}"
APPLIED_MIGRATIONS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT version FROM schema_migrations ORDER BY version;" 2>/dev/null || echo "")

# Count applied migrations
APPLIED_COUNT=$(echo "$APPLIED_MIGRATIONS" | grep -c -v '^$')
echo "Applied migrations: $APPLIED_COUNT"

if [ "$APPLIED_COUNT" -gt 0 ]; then
    echo "Latest applied migration: $(echo "$APPLIED_MIGRATIONS" | tail -1 | tr -d '[:space:]')"
fi
echo ""

# Find all migration files
MIGRATION_FILES=$(find "$MIGRATIONS_DIR" -name "V*.sql" -type f | sort)

if [ -z "$MIGRATION_FILES" ]; then
    echo -e "${YELLOW}No migration files found in $MIGRATIONS_DIR${NC}"
    exit 0
fi

# Count total migrations
TOTAL_MIGRATIONS=$(echo "$MIGRATION_FILES" | wc -l)
echo "Total migration files found: $TOTAL_MIGRATIONS"
echo ""

# Execute pending migrations
MIGRATIONS_RUN=0
MIGRATIONS_SKIPPED=0

for migration_file in $MIGRATION_FILES; do
    # Extract version from filename (V001__description.sql -> 001)
    filename=$(basename "$migration_file")
    version=$(echo "$filename" | sed 's/V\([0-9]*\)__.*/\1/')
    # shellcheck disable=SC2001
    description=$(echo "$filename" | sed 's/V[0-9]*__\(.*\)\.sql/\1/' | tr '_' ' ')

    # Check if migration is already applied
    if echo "$APPLIED_MIGRATIONS" | grep -q "^[[:space:]]*${version}[[:space:]]*$"; then
        echo -e "${BLUE}[SKIP]${NC} V$version - $description (already applied)"
        MIGRATIONS_SKIPPED=$((MIGRATIONS_SKIPPED + 1))
        continue
    fi

    # Execute migration
    echo -e "${YELLOW}[RUN]${NC} V$version - $description"

    MIGRATION_START=$(date +%s)

    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$migration_file"; then
        MIGRATION_END=$(date +%s)
        DURATION=$((MIGRATION_END - MIGRATION_START))
        DURATION_MS=$((DURATION * 1000))

        # Calculate checksum
        CHECKSUM=$(md5sum "$migration_file" | awk '{print $1}')

        # Record migration (if not self-recording)
        if [ "$version" != "001" ]; then
            psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
                "INSERT INTO schema_migrations (version, description, execution_time_ms, checksum)
                 VALUES ('$version', '$description', $DURATION_MS, '$CHECKSUM')
                 ON CONFLICT (version) DO NOTHING;" > /dev/null
        fi

        echo -e "${GREEN}[SUCCESS]${NC} V$version completed in ${DURATION}s"
        MIGRATIONS_RUN=$((MIGRATIONS_RUN + 1))
    else
        echo -e "${RED}[FAILED]${NC} V$version migration failed!"
        echo -e "${RED}Migration stopped at V$version${NC}"
        exit 1
    fi

    echo ""
done

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Migration Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Total migrations found: $TOTAL_MIGRATIONS"
echo "Migrations executed: $MIGRATIONS_RUN"
echo "Migrations skipped: $MIGRATIONS_SKIPPED"
echo ""

if [ $MIGRATIONS_RUN -eq 0 ]; then
    echo -e "${GREEN}✓ Database is up to date${NC}"
else
    echo -e "${GREEN}✓ Successfully applied $MIGRATIONS_RUN migration(s)${NC}"
fi

# Show current migration status
echo ""
echo -e "${YELLOW}Current migration status:${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
    "SELECT version, description, applied_at,
            ROUND(execution_time_ms::NUMERIC / 1000, 2) as execution_sec
     FROM schema_migrations
     ORDER BY version DESC
     LIMIT 10;"
