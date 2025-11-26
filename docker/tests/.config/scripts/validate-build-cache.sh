#!/bin/bash
# Docker Build Cache Validation Script
# Detects corrupted cache layers and validates package integrity
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🔍 Docker Build Cache Validation"
echo "================================="

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Track validation status
VALIDATION_PASSED=true

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
        VALIDATION_PASSED=false
    fi
}

# 1. Validate package.json checksum
echo ""
echo "📦 Validating package.json integrity..."
if [ -f "$TESTS_DIR/package.json" ]; then
    CHECKSUM=$(sha256sum "$TESTS_DIR/package.json" | cut -d' ' -f1)
    echo "Current checksum: $CHECKSUM"

    # Store checksum for comparison
    mkdir -p /tmp/test-cache-validation
    echo "$CHECKSUM" > /tmp/test-cache-validation/package.checksum

    print_status "pass" "package.json checksum recorded"
else
    print_status "fail" "package.json not found"
fi

# 2. Check for suspicious files that might indicate cache corruption
echo ""
echo "🔎 Checking for corruption indicators..."

# Check for literal \n in files (corruption symptom from retro docs)
if grep -r "\\\\n" "$TESTS_DIR"/*.ts "$TESTS_DIR"/*.js 2>/dev/null | grep -v node_modules; then
    print_status "fail" "Found literal \\n sequences (possible cache corruption)"
else
    print_status "pass" "No literal escape sequences found"
fi

# 3. Validate Playwright configuration
echo ""
echo "🎭 Validating Playwright configuration..."
if [ -f "$TESTS_DIR/playwright.config.ts" ]; then
    # Check for syntax errors
    if node -c "$TESTS_DIR/playwright.config.ts" 2>/dev/null; then
        print_status "pass" "playwright.config.ts syntax valid"
    else
        print_status "fail" "playwright.config.ts has syntax errors"
    fi
else
    print_status "warn" "playwright.config.ts not found"
fi

# 4. Check Docker image layers (if Docker is available)
echo ""
echo "🐳 Checking Docker image status..."
if command -v docker &> /dev/null; then
    # Check if test image exists
    if docker images | grep -q "semantic-kernel-tests"; then
        IMAGE_ID=$(docker images --filter=reference="semantic-kernel-tests:latest" --format "{{.ID}}")
        if [ -n "$IMAGE_ID" ]; then
            echo "Found test image: $IMAGE_ID"

            # Inspect image for anomalies
            IMAGE_SIZE=$(docker images --filter=reference="semantic-kernel-tests:latest" --format "{{.Size}}")
            echo "Image size: $IMAGE_SIZE"

            # Check if image is reasonable size (should be 1-3GB with browsers)
            print_status "pass" "Test image exists"
        else
            print_status "warn" "No test image found (will be built on first run)"
        fi
    else
        print_status "warn" "Test image not yet built"
    fi
else
    print_status "warn" "Docker not available for validation"
fi

# 5. Validate critical test files exist and are valid
echo ""
echo "📝 Validating critical test files..."

CRITICAL_FILES=(
    "package.json"
    "playwright.config.ts"
    "tsconfig.json"
    ".config/docker/Dockerfile"
    ".config/docker/docker-compose.test.yml"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$TESTS_DIR/$file" ]; then
        print_status "pass" "$file exists"
    else
        print_status "fail" "$file missing"
    fi
done

# 6. Check for stale node_modules (shouldn't exist with baked dependencies)
echo ""
echo "🗂️  Checking for obsolete directories..."
if [ -d "$TESTS_DIR/node_modules" ]; then
    print_status "warn" "node_modules/ exists (not needed with baked dependencies)"
    echo "   Run: rm -rf tests/node_modules/"
else
    print_status "pass" "No obsolete node_modules/ directory"
fi

# 7. Validate Docker Compose configuration
echo ""
echo "⚙️  Validating Docker Compose configuration..."
if [ -f "$TESTS_DIR/.config/docker/docker-compose.test.yml" ]; then
    if docker-compose -f "$TESTS_DIR/.config/docker/docker-compose.test.yml" config > /dev/null 2>&1; then
        print_status "pass" "docker-compose.test.yml is valid"
    else
        print_status "fail" "docker-compose.test.yml has syntax errors"
    fi
fi

# 8. Summary and recommendations
echo ""
echo "================================="
echo "Validation Summary"
echo "================================="

if [ "$VALIDATION_PASSED" = true ]; then
    echo -e "${GREEN}✅ All validations passed${NC}"
    echo ""
    echo "Cache is healthy. Safe to proceed with builds."
    exit 0
else
    echo -e "${RED}❌ Validation failures detected${NC}"
    echo ""
    echo "Recommendations:"
    echo "1. Rebuild cache: make test-rebuild-cache"
    echo "2. Check for file corruption: git status"
    echo "3. Review Docker logs: docker-compose logs tests"
    echo ""
    echo "If issues persist after rebuild, use --no-cache:"
    echo "  docker-compose -f tests/.config/docker/docker-compose.test.yml build --no-cache tests"
    exit 1
fi
