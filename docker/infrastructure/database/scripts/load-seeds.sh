#!/bin/bash
# Database Seed Data Loader
# Purpose: Load seed data for development/test environments
# Usage: ./load-seeds.sh [environment]

set -e  # Exit on error

# Configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-semantic_kernel}"
DB_USER="${DB_USER:-user}"
SEEDS_DIR="${SEEDS_DIR:-/seeds}"
ENVIRONMENT="${1:-development}"  # development, test, production

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Database Seed Data Loader${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Database: $DB_NAME"
echo "Seeds Directory: $SEEDS_DIR"
echo "Environment: $ENVIRONMENT"
echo ""

# Check if production environment
if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}⚠️  WARNING: PRODUCTION ENVIRONMENT${NC}"
    echo -e "${RED}========================================${NC}"
    echo "Loading seed data in PRODUCTION is not recommended!"
    echo "Seed data contains test accounts and demo data."
    echo ""
    read -p "Are you ABSOLUTELY SURE? (type 'yes-load-seeds-in-production'): " CONFIRM

    if [ "$CONFIRM" != "yes-load-seeds-in-production" ]; then
        echo -e "${YELLOW}Seed loading cancelled.${NC}"
        exit 0
    fi
fi

# Check if seeds directory exists
if [ ! -d "$SEEDS_DIR" ]; then
    echo -e "${RED}Error: Seeds directory not found: $SEEDS_DIR${NC}"
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

# Find all seed files: support .sql and .pgsql
SEED_FILES=$(find "$SEEDS_DIR" \( -name "*.sql" -o -name "*.pgsql" \) -type f ! -name "README*" | sort)

if [ -z "$SEED_FILES" ]; then
    echo -e "${YELLOW}No seed files found in $SEEDS_DIR${NC}"
    exit 0
fi

# Count total seeds
TOTAL_SEEDS=$(echo "$SEED_FILES" | wc -l)
echo "Total seed files found: $TOTAL_SEEDS"
echo ""

# Confirm loading
echo -e "${YELLOW}The following seed files will be loaded:${NC}"
for seed_file in $SEED_FILES; do
    echo "  - $(basename "$seed_file")"
done
echo ""

if [ "$ENVIRONMENT" != "production" ]; then
    read -p "Continue loading seeds? (y/N): " CONFIRM
    if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
        echo -e "${YELLOW}Seed loading cancelled.${NC}"
        exit 0
    fi
    echo ""
fi

# Load seed files
SEEDS_LOADED=0
SEEDS_FAILED=0

for seed_file in $SEED_FILES; do
    filename=$(basename "$seed_file")
    echo -e "${YELLOW}[LOADING]${NC} $filename"

    SEED_START=$(date +%s)

    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$seed_file" > /dev/null 2>&1; then
        SEED_END=$(date +%s)
        DURATION=$((SEED_END - SEED_START))

        echo -e "${GREEN}[SUCCESS]${NC} $filename loaded in ${DURATION}s"
        SEEDS_LOADED=$((SEEDS_LOADED + 1))
    else
        echo -e "${RED}[FAILED]${NC} $filename failed to load!"
        SEEDS_FAILED=$((SEEDS_FAILED + 1))
    fi

    echo ""
done

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Seed Loading Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Total seed files: $TOTAL_SEEDS"
echo "Successfully loaded: $SEEDS_LOADED"
echo "Failed: $SEEDS_FAILED"
echo ""

if [ $SEEDS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All seed data loaded successfully${NC}"
else
    echo -e "${RED}⚠ Some seed files failed to load${NC}"
fi

# Show database statistics
echo ""
echo -e "${YELLOW}Database statistics after seeding:${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
    "SELECT
        (SELECT COUNT(*) FROM users) as users,
        (SELECT COUNT(*) FROM conversations) as conversations,
        (SELECT COUNT(*) FROM messages) as messages,
        (SELECT COUNT(*) FROM skills) as skills,
        (SELECT COUNT(*) FROM semantic_memories) as semantic_memories,
        (SELECT COUNT(*) FROM embeddings) as embeddings;"

echo ""
echo -e "${YELLOW}⚠️  Remember: Default password for dev users is 'Dev@12345'${NC}"
echo -e "${YELLOW}⚠️  Change passwords in shared environments!${NC}"
