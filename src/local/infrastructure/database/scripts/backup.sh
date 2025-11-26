#!/bin/bash
# Database Backup Script
# Purpose: Create PostgreSQL database backups with metadata tracking
# Usage: ./backup.sh [backup_name] [backup_type]

set -e  # Exit on error

# Configuration
DB_HOST="${DB_HOST:-database}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-semantic_kernel}"
DB_USER="${DB_USER:-user}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
BACKUP_TYPE="${2:-full}"  # full, incremental, differential
BACKUP_NAME="${1:-backup_$(date +%Y%m%d_%H%M%S)}"
COMPRESSION="${COMPRESSION:-gzip}"

# Colors for output
# shellcheck disable=SC2034
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Database Backup Utility${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Backup Name: $BACKUP_NAME"
echo "Backup Type: $BACKUP_TYPE"
echo "Database: $DB_NAME"
echo "Compression: $COMPRESSION"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate backup file path
BACKUP_FILE="$BACKUP_DIR/${BACKUP_NAME}.sql"
if [ "$COMPRESSION" = "gzip" ]; then
    BACKUP_FILE="${BACKUP_FILE}.gz"
fi

# Record backup start in database
echo -e "${YELLOW}Recording backup start...${NC}"
BACKUP_ID=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT start_backup('${BACKUP_NAME}', '${BACKUP_TYPE}', '${BACKUP_FILE}');")
BACKUP_ID=$(echo "$BACKUP_ID" | tr -d '[:space:]')

echo "Backup ID: $BACKUP_ID"

# Start backup
BACKUP_START=$(date +%s)
echo -e "${YELLOW}Starting database backup...${NC}"

if [ "$COMPRESSION" = "gzip" ]; then
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --format=plain \
        --verbose \
        --no-owner \
        --no-acl \
        2>&1 | gzip > "$BACKUP_FILE"
else
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --format=plain \
        --verbose \
        --no-owner \
        --no-acl \
        --file="$BACKUP_FILE"
fi

BACKUP_END=$(date +%s)
DURATION=$((BACKUP_END - BACKUP_START))

# Get backup file size
BACKUP_SIZE=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE" 2>/dev/null)

# Calculate checksum
echo -e "${YELLOW}Calculating checksum...${NC}"
CHECKSUM=$(md5sum "$BACKUP_FILE" | awk '{print $1}')

# Record backup completion
echo -e "${YELLOW}Recording backup completion...${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
    "SELECT complete_backup('${BACKUP_ID}', ${BACKUP_SIZE}, '${CHECKSUM}', TRUE, NULL);" > /dev/null

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Backup Completed Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Backup File: $BACKUP_FILE"
echo "File Size: $(numfmt --to=iec-i --suffix=B "$BACKUP_SIZE" 2>/dev/null || echo "${BACKUP_SIZE}" bytes)"
echo "Duration: ${DURATION} seconds"
echo "Checksum: $CHECKSUM"
echo ""

# Show recent backups
echo -e "${YELLOW}Recent backups:${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
    "SELECT backup_name, backup_type, file_size, created_at
     FROM v_backup_overview
     ORDER BY created_at DESC
     LIMIT 5;"

echo ""
echo -e "${GREEN}Backup saved to: $BACKUP_FILE${NC}"
