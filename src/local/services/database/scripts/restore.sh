#!/bin/bash
# Database Restore Script
# Purpose: Restore PostgreSQL database from backup
# Usage: ./restore.sh <backup_file> [restore_type]

set -e  # Exit on error

# Configuration
DB_HOST="${DB_HOST:-database}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-semantic_kernel}"
DB_USER="${DB_USER:-user}"
BACKUP_FILE="$1"
RESTORE_TYPE="${2:-full}"  # full, partial, point_in_time

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if [ -z "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not specified${NC}"
    echo "Usage: $0 <backup_file> [restore_type]"
    echo ""
    echo "Available backups:"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
        "SELECT backup_name, backup_type, file_size, created_at
         FROM v_backup_overview
         WHERE status = 'completed'
         ORDER BY created_at DESC
         LIMIT 10;"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}⚠️  WARNING: DATABASE RESTORE${NC}"
echo -e "${YELLOW}========================================${NC}"
echo "This will restore the database from:"
echo "  File: $BACKUP_FILE"
echo "  Type: $RESTORE_TYPE"
echo "  Target Database: $DB_NAME"
echo ""
echo -e "${RED}This operation will OVERWRITE existing data!${NC}"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${YELLOW}Restore cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Starting Database Restore${NC}"
echo -e "${GREEN}========================================${NC}"

# Get backup metadata if it exists
BACKUP_ID=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT id FROM backup_metadata WHERE file_path = '${BACKUP_FILE}' LIMIT 1;" 2>/dev/null || echo "")
BACKUP_ID=$(echo "$BACKUP_ID" | tr -d '[:space:]')

# Record restore start
echo -e "${YELLOW}Recording restore start...${NC}"
if [ -n "$BACKUP_ID" ]; then
    RESTORE_ID=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c \
        "SELECT start_restore('${BACKUP_ID}', '${RESTORE_TYPE}', NULL);")
else
    RESTORE_ID=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c \
        "SELECT start_restore(NULL, '${RESTORE_TYPE}', NULL);")
fi
RESTORE_ID=$(echo "$RESTORE_ID" | tr -d '[:space:]')

echo "Restore ID: $RESTORE_ID"

# Start restore
RESTORE_START=$(date +%s)
echo -e "${YELLOW}Restoring database...${NC}"

# Determine if file is compressed
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "Decompressing and restoring..."
    gunzip -c "$BACKUP_FILE" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"
else
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < "$BACKUP_FILE"
fi

RESTORE_END=$(date +%s)
DURATION=$((RESTORE_END - RESTORE_START))

# Count restored rows (approximate)
echo -e "${YELLOW}Counting restored rows...${NC}"
TOTAL_ROWS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT SUM(n_live_tup) FROM pg_stat_user_tables;")
TOTAL_ROWS=$(echo "$TOTAL_ROWS" | tr -d '[:space:]')

# Record restore completion
echo -e "${YELLOW}Recording restore completion...${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
    "SELECT complete_restore('${RESTORE_ID}', ${TOTAL_ROWS}, TRUE, NULL);" > /dev/null

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Restore Completed Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Duration: ${DURATION} seconds"
echo "Rows Restored: $TOTAL_ROWS"
echo ""

# Run database statistics
echo -e "${YELLOW}Database statistics after restore:${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
    "SELECT * FROM get_database_statistics();"

echo ""
echo -e "${GREEN}Restore completed from: $BACKUP_FILE${NC}"
echo -e "${YELLOW}⚠️  Remember to verify application functionality!${NC}"
