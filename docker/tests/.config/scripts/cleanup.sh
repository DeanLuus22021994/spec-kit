#!/bin/bash
set -e

echo "🧹 Cleaning up test environment..."
echo "=================================="

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
CLEAN_DB="${CLEAN_DB:-false}"
CLEAN_VOLUMES="${CLEAN_VOLUMES:-false}"
TEST_DIR="/app/tests"

# Function to print status
print_status() {
    local status=$1
    local message=$2

    if [ "$status" = "pass" ]; then
        echo -e "${GREEN}✅${NC} $message"
    elif [ "$status" = "warn" ]; then
        echo -e "${YELLOW}⚠️${NC} $message"
    else
        echo -e "${RED}❌${NC} $message"
    fi
}

# Function to clean directory with verification
clean_directory() {
    local dir=$1
    local description=$2

    if [ -d "$dir" ]; then
        local size=$(du -sh "$dir" 2>/dev/null | cut -f1 || echo "unknown")
        echo "Cleaning $description ($size)..."
        rm -rf "$dir"

        if [ -d "$dir" ]; then
            print_status "fail" "$description cleanup failed - directory still exists"
            return 1
        else
            print_status "pass" "$description cleaned successfully ($size freed)"
            return 0
        fi
    else
        print_status "pass" "$description already clean (directory does not exist)"
        return 0
    fi
}

# Function to clean files by pattern with verification
clean_files() {
    local pattern=$1
    local description=$2

    local file_count=$(find "$TEST_DIR" -name "$pattern" -type f 2>/dev/null | wc -l)

    if [ "$file_count" -gt 0 ]; then
        echo "Cleaning $file_count $description files..."
        find "$TEST_DIR" -name "$pattern" -type f -delete

        local remaining=$(find "$TEST_DIR" -name "$pattern" -type f 2>/dev/null | wc -l)
        if [ "$remaining" -eq 0 ]; then
            print_status "pass" "$description files cleaned ($file_count removed)"
            return 0
        else
            print_status "warn" "$description cleanup incomplete ($remaining files remain)"
            return 1
        fi
    else
        print_status "pass" "No $description files to clean"
        return 0
    fi
}

# Change to test directory
cd "$TEST_DIR"

# Clean test artifacts
echo ""
echo "1️⃣ Cleaning test artifacts..."
clean_directory "$TEST_DIR/playwright-report" "Playwright reports"
clean_directory "$TEST_DIR/test-results" "Test results"
clean_directory "$TEST_DIR/.playwright-cache" "Playwright cache"
clean_directory "$TEST_DIR/coverage" "Coverage reports"
clean_directory "$TEST_DIR/.nyc_output" "NYC coverage output"

# Clean temporary files
echo ""
echo "2️⃣ Cleaning temporary files..."
clean_files "*.log" "Log"
clean_files "npm-debug.log*" "NPM debug log"
clean_files ".DS_Store" "macOS metadata"
clean_files "Thumbs.db" "Windows thumbnail cache"

# Clean obsolete directories
echo ""
echo "3️⃣ Checking for obsolete directories..."
if [ -d "$TEST_DIR/node_modules" ]; then
    print_status "warn" "Found node_modules/ - should not exist with baked dependencies"
    echo "    Remove with: docker-compose -f .config/docker/docker-compose.test.yml down && make test-rebuild-cache"
else
    print_status "pass" "No obsolete directories found"
fi

# Clean Docker containers (if requested)
if [ "$CLEAN_VOLUMES" = "true" ]; then
    echo ""
    echo "4️⃣ Cleaning Docker test containers..."

    if docker-compose -f .config/docker/docker-compose.test.yml ps -q tests &>/dev/null 2>&1; then
        echo "Stopping test containers..."
        docker-compose -f .config/docker/docker-compose.test.yml down

        # Verify containers stopped
        if ! docker-compose -f .config/docker/docker-compose.test.yml ps -q tests &>/dev/null 2>&1; then
            print_status "pass" "Test containers stopped"
        else
            print_status "warn" "Test containers may still be running"
        fi
    else
        print_status "pass" "No test containers running"
    fi
else
    echo ""
    echo "4️⃣ Skipping Docker cleanup (set CLEAN_VOLUMES=true to enable)"
fi

# Clean database (optional)
if [ "$CLEAN_DB" = "true" ]; then
    echo ""
    echo "5️⃣ Cleaning test database..."

    DB_HOST="${DB_HOST:-database}"
    DB_PORT="${DB_PORT:-5432}"
    DB_USER="${DB_USER:-user}"
    DB_NAME="${DB_NAME:-semantic_kernel_test}"
    DB_PASSWORD="${DB_PASSWORD:-test_password}"

    export PGPASSWORD="$DB_PASSWORD"

    # Check if database is accessible
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" &>/dev/null; then
        echo "Truncating test tables..."

        if psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" <<-EOSQL 2>/dev/null
            TRUNCATE TABLE embeddings CASCADE;
            TRUNCATE TABLE conversations CASCADE;
            TRUNCATE TABLE users CASCADE;
EOSQL
        then
            print_status "pass" "Test database tables truncated"
        else
            print_status "warn" "Database truncation failed (tables may not exist)"
        fi
    else
        print_status "warn" "Database not accessible (may already be stopped)"
    fi
else
    echo ""
    echo "5️⃣ Skipping database cleanup (set CLEAN_DB=true to enable)"
fi

# Verify cleanup
echo ""
echo "=================================="
echo "Cleanup Verification"
echo "=================================="

ISSUES=0

# Check directories
for dir in "playwright-report" "test-results" ".playwright-cache" "coverage" ".nyc_output"; do
    if [ -d "$TEST_DIR/$dir" ]; then
        print_status "warn" "Directory still exists: $dir"
        ISSUES=$((ISSUES + 1))
    fi
done

# Check log files
LOG_COUNT=$(find "$TEST_DIR" -name "*.log" -type f 2>/dev/null | wc -l)
if [ "$LOG_COUNT" -gt 0 ]; then
    print_status "warn" "Found $LOG_COUNT log files remaining"
    ISSUES=$((ISSUES + 1))
fi

# Check disk space freed
if command -v du &>/dev/null; then
    DISK_USAGE=$(du -sh "$TEST_DIR" 2>/dev/null | cut -f1 || echo "unknown")
    echo "Current test directory size: $DISK_USAGE"
fi

# Summary
echo ""
echo "=================================="
if [ $ISSUES -eq 0 ]; then
    print_status "pass" "Cleanup completed successfully - no issues detected"
    echo ""
    echo "Next steps:"
    echo "  - Run tests: make test-docker"
    echo "  - Clean database: CLEAN_DB=true .config/scripts/cleanup.sh"
    echo "  - Clean volumes: CLEAN_VOLUMES=true .config/scripts/cleanup.sh"
    exit 0
else
    print_status "warn" "Cleanup completed with $ISSUES issues"
    echo ""
    echo "Manual cleanup may be required:"
    echo "  - Remove containers: docker-compose -f .config/docker/docker-compose.test.yml down -v"
    echo "  - Remove directories: rm -rf $TEST_DIR/{playwright-report,test-results,coverage}"
    exit 1
fi
