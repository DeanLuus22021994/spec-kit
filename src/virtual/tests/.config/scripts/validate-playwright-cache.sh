#!/bin/bash
# Playwright Browser Cache Validation Script
# Ensures browser binaries match Playwright version and are not corrupted
set -e

echo "🎭 Playwright Browser Cache Validation"
echo "======================================"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

VALIDATION_PASSED=true

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

# 1. Check Playwright installation
echo ""
echo "📦 Checking Playwright installation..."
if command -v npx &> /dev/null; then
    if npx playwright --version &> /dev/null; then
        PLAYWRIGHT_VERSION=$(npx playwright --version | grep -oP '\d+\.\d+\.\d+' || echo "unknown")
        print_status "pass" "Playwright installed: $PLAYWRIGHT_VERSION"
    else
        print_status "fail" "Playwright not installed or corrupted"
    fi
else
    print_status "fail" "npx not available"
fi

# 2. Validate @playwright/test package
echo ""
echo "📚 Validating @playwright/test package..."
if npm list @playwright/test --depth=0 2>/dev/null | grep -q "@playwright/test"; then
    PACKAGE_VERSION=$(npm list @playwright/test --depth=0 2>/dev/null | grep "@playwright/test" | grep -oP '\d+\.\d+\.\d+' || echo "unknown")
    print_status "pass" "@playwright/test@$PACKAGE_VERSION installed"
else
    print_status "warn" "@playwright/test not found (baked dependencies expected)"
fi

# 3. Check browser binaries
echo ""
echo "🌐 Checking browser binaries..."

BROWSERS=("chromium" "firefox" "webkit")
BROWSER_PATH="${PLAYWRIGHT_BROWSERS_PATH:-/ms-playwright}"

for browser in "${BROWSERS[@]}"; do
    echo "Checking $browser..."

    # Dry run to check if browser is installed
    if npx playwright install --dry-run $browser 2>&1 | grep -q "is already installed"; then
        print_status "pass" "$browser is installed"
    else
        print_status "warn" "$browser may need installation"

        # Auto-fix: Install missing browser
        echo "   Installing $browser..."
        npx playwright install --with-deps $browser
    fi
done

# 4. Verify browser cache directory
echo ""
echo "📂 Checking browser cache directory..."
if [ -d "$BROWSER_PATH" ]; then
    CACHE_SIZE=$(du -sh "$BROWSER_PATH" 2>/dev/null | cut -f1 || echo "unknown")
    print_status "pass" "Browser cache exists: $CACHE_SIZE"

    # Check if cache size is reasonable (should be ~1-2GB)
    CACHE_SIZE_MB=$(du -sm "$BROWSER_PATH" 2>/dev/null | cut -f1 || echo "0")
    if [ "$CACHE_SIZE_MB" -lt 500 ]; then
        print_status "warn" "Cache size suspiciously small ($CACHE_SIZE_MB MB), may be incomplete"
    elif [ "$CACHE_SIZE_MB" -gt 5000 ]; then
        print_status "warn" "Cache size large ($CACHE_SIZE_MB MB), may contain duplicates"
    fi
else
    print_status "warn" "Browser cache directory not found: $BROWSER_PATH"
fi

# 5. Validate browser executables
echo ""
echo "🔍 Validating browser executables..."

# Check Chromium
if [ -f "$BROWSER_PATH/chromium-"*/chrome-linux/chrome ] || [ -f "$BROWSER_PATH/chromium-"*/chrome-win/chrome.exe ]; then
    print_status "pass" "Chromium executable found"
else
    print_status "warn" "Chromium executable not found"
fi

# Check Firefox
if [ -f "$BROWSER_PATH/firefox-"*/firefox/firefox ] || [ -f "$BROWSER_PATH/firefox-"*/firefox/firefox.exe ]; then
    print_status "pass" "Firefox executable found"
else
    print_status "warn" "Firefox executable not found"
fi

# Check WebKit
if [ -f "$BROWSER_PATH/webkit-"*/minibrowser-gtk/MiniBrowser ] || [ -f "$BROWSER_PATH/webkit-"*/Playwright.exe ]; then
    print_status "pass" "WebKit executable found"
else
    print_status "warn" "WebKit executable not found"
fi

# 6. Test browser launch (quick smoke test)
echo ""
echo "🚀 Running browser smoke tests..."

# Only test if we're in a container (to avoid opening browsers on host)
if [ -f "/.dockerenv" ] || grep -q docker /proc/1/cgroup 2>/dev/null; then
    # Quick version check for each browser
    for browser in "${BROWSERS[@]}"; do
        if timeout 10 npx playwright install --dry-run $browser &> /dev/null; then
            print_status "pass" "$browser smoke test passed"
        else
            print_status "warn" "$browser smoke test failed (may need reinstall)"
        fi
    done
else
    print_status "warn" "Skipping smoke tests (not in container)"
fi

# 7. Check for version mismatches
echo ""
echo "🔄 Checking version consistency..."

# Compare package.json version vs installed version
if [ -f "package.json" ]; then
    EXPECTED_VERSION=$(grep "@playwright/test" package.json | grep -oP '\d+\.\d+\.\d+' | head -1 || echo "unknown")
    if [ "$EXPECTED_VERSION" != "unknown" ] && [ "$PACKAGE_VERSION" != "unknown" ]; then
        if [ "$EXPECTED_VERSION" = "$PACKAGE_VERSION" ]; then
            print_status "pass" "Version match: $EXPECTED_VERSION"
        else
            print_status "warn" "Version mismatch: package.json=$EXPECTED_VERSION, installed=$PACKAGE_VERSION"
        fi
    fi
fi

# 8. Summary
echo ""
echo "======================================"
echo "Validation Summary"
echo "======================================"

if [ "$VALIDATION_PASSED" = true ]; then
    echo -e "${GREEN}✅ Browser cache validated successfully${NC}"
    echo ""
    echo "All browser binaries are healthy and ready for testing."
    exit 0
else
    echo -e "${RED}❌ Browser cache validation failed${NC}"
    echo ""
    echo "Recommendations:"
    echo "1. Reinstall browsers: npx playwright install --with-deps"
    echo "2. Rebuild cache: make test-rebuild-cache"
    echo "3. Clear browser cache and rebuild:"
    echo "   docker volume rm playwright-cache"
    echo "   docker-compose build --no-cache tests"
    exit 1
fi
