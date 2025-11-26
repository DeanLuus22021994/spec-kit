#!/bin/bash
set -e

echo "🎭 Playwright Test Runner"
echo "========================="

# Wait for services to be healthy
echo "⏳ Waiting for services..."
timeout 60 bash -c 'until curl -f http://frontend:3000 > /dev/null 2>&1; do sleep 2; done'
timeout 60 bash -c 'until curl -f http://backend:80/health > /dev/null 2>&1; do sleep 2; done'

echo "✅ Services ready"

# Validate Playwright browser cache before running tests
echo "🔍 Validating browser cache..."
if [ -f "/app/tests/.config/scripts/validate-playwright-cache.sh" ]; then
    bash /app/tests/.config/scripts/validate-playwright-cache.sh || {
        echo "⚠️  Browser cache validation failed, attempting auto-repair..."
        npx playwright install --with-deps chromium firefox webkit
    }
else
    echo "⚠️  Validation script not found, skipping cache check"
fi

echo "🚀 Running tests..."

# Change to test directory
cd /app/tests

# Run tests with appropriate reporter
if [ "$CI" = "true" ]; then
    npx playwright test --reporter=html --reporter=junit
else
    npx playwright test
fi

echo "✅ Tests complete"
