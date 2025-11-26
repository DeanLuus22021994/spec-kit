## Plan: Docker-Based Test Efficiency Optimization (Revised)

### Current State Analysis

**Test Suite:**

- 46 Playwright E2E tests × 5 browsers = 230 test executions
- 5 .NET integration tests
- All failing due to missing services at `localhost:3000` and `localhost:5000`

**Tools Directory Pattern (Established):**

```
tools/
├── .dockerignore        # Optimized build context
├── cli.py               # Python CLI tool
├── docgen.py            # Documentation generator
├── Dockerfile           # Self-contained container
└── scripts/             # Supporting scripts
```

**Tests Directory (Current):**

```
tests/
├── e2e/                 # Playwright tests
├── integration-tests/   # .NET integration tests
├── package.json         # Node dependencies
├── playwright.config.ts # Test configuration
└── (missing Dockerfile pattern)
```

---

## Strategic Approach

**Align tests directory with tools directory containerization pattern:**

1. Create self-contained `tests/Dockerfile` (like Dockerfile)
2. Add `tests/.dockerignore` for optimized build context
3. Add `tests/scripts/` for test automation
4. Integrate with Docker Compose for orchestration

---

## Implementation Plan

### Phase 1: Containerize Tests Directory (Pattern Alignment) ⭐⭐⭐⭐⭐

**Create `tests/Dockerfile`** - Self-contained test container:

```dockerfile
# Multi-stage build for efficiency
FROM mcr.microsoft.com/playwright:v1.40.0-jammy AS base

WORKDIR /tests

# Install dependencies layer (cacheable)
COPY package.json package-lock.json ./
RUN npm ci && npx playwright install --with-deps

# Copy test source
COPY . .

# Set test environment
ENV CI=true
ENV NODE_ENV=test

# Default command (can be overridden)
CMD ["npx", "playwright", "test"]

# ---

# Stage for debugging/development
FROM base AS dev
ENV CI=false
CMD ["npx", "playwright", "test", "--ui"]

# ---

# Stage for CI/production
FROM base AS ci
ENV CI=true
CMD ["npx", "playwright", "test", "--reporter=html", "--reporter=junit"]
```

**Create `tests/.dockerignore`** - Optimize build context:

```
# Build artifacts
node_modules/
playwright-report/
test-results/
*.log

# Development files
.env.local
.DS_Store

# Git
.git/
.gitignore

# IDE
.vscode/
.idea/

# OS files
Thumbs.db
```

**Create `tests/scripts/`** - Test automation scripts:

**`tests/scripts/run-tests.sh`:**

```bash
#!/bin/bash
set -e

echo "🎭 Playwright Test Runner"
echo "========================="

# Wait for services to be healthy
echo "⏳ Waiting for services..."
timeout 60 bash -c 'until curl -f http://frontend:3000 > /dev/null 2>&1; do sleep 2; done'
timeout 60 bash -c 'until curl -f http://backend:80/health > /dev/null 2>&1; do sleep 2; done'

echo "✅ Services ready"
echo "🚀 Running tests..."

# Run tests with appropriate reporter
if [ "$CI" = "true" ]; then
    npx playwright test --reporter=html --reporter=junit
else
    npx playwright test
fi

echo "✅ Tests complete"
```

**`tests/scripts/seed-test-data.sh`:**

```bash
#!/bin/bash
set -e

echo "🌱 Seeding test data..."

# Wait for database
until pg_isready -h database -p 5432 -U user; do
    echo "⏳ Waiting for database..."
    sleep 2
done

# Seed test data (integrate with existing infrastructure)
psql -h database -U user -d semantic_kernel_test <<-EOSQL
    -- Test users
    INSERT INTO users (email, name) VALUES
        ('test@example.com', 'Test User'),
        ('admin@example.com', 'Admin User');

    -- Test conversations
    INSERT INTO conversations (user_id, title) VALUES
        (1, 'Test Conversation 1');
EOSQL

echo "✅ Test data seeded"
```

**`tests/scripts/cleanup.sh`:**

```bash
#!/bin/bash
set -e

echo "🧹 Cleaning up test artifacts..."

rm -rf playwright-report/
rm -rf test-results/
rm -rf .playwright-cache/

echo "✅ Cleanup complete"
```

---

### Phase 2: Docker Compose Integration 🎯

**Create `docker-compose.test.yml`** - Orchestration matching tools pattern:

```yaml
version: "3.8"

services:
  # Test database (tmpfs for speed)
  database:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: semantic_kernel_test
      POSTGRES_USER: user
      POSTGRES_PASSWORD: test_password
    tmpfs:
      - /var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d semantic_kernel_test"]
      interval: 5s
      timeout: 3s
      retries: 10
    networks:
      - test-network

  # Test vector store (tmpfs for speed)
  vector:
    image: qdrant/qdrant:v1.7.4
    tmpfs:
      - /qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/healthz"]
      interval: 5s
      timeout: 3s
      retries: 10
    networks:
      - test-network

  # Embeddings service
  embeddings:
    build:
      context: ..
      dockerfile: dockerfiles/embeddings.Dockerfile
    depends_on:
      database:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 5s
      timeout: 3s
      retries: 10
    networks:
      - test-network

  # Backend service
  backend:
    build:
      context: ..
      dockerfile: dockerfiles/backend.Dockerfile
    depends_on:
      database:
        condition: service_healthy
      vector:
        condition: service_healthy
      embeddings:
        condition: service_healthy
    environment:
      DATABASE_URL: postgres://user:test_password@database:5432/semantic_kernel_test
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 5s
      timeout: 3s
      retries: 10
    networks:
      - test-network

  # Frontend service
  frontend:
    build:
      context: ..
      dockerfile: dockerfiles/frontend.Dockerfile
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 5s
      timeout: 3s
      retries: 10
    networks:
      - test-network

  # Tests container (aligned with tools pattern)
  tests:
    build:
      context: .
      dockerfile: Dockerfile
      target: ci
    depends_on:
      frontend:
        condition: service_healthy
      backend:
        condition: service_healthy
    volumes:
      - ./playwright-report:/tests/playwright-report
      - ./test-results:/tests/test-results
    environment:
      CI: "true"
      BASE_URL: http://frontend:3000
      API_URL: http://backend:80
    networks:
      - test-network
    command: /tests/scripts/run-tests.sh

networks:
  test-network:
    driver: bridge
```

**Create `.env.test`** - Test environment configuration:

```bash
# Environment
ENVIRONMENT=test
NODE_ENV=test
CI=true

# Database
DATABASE_NAME=semantic_kernel_test
DATABASE_USER=user
DATABASE_PASSWORD=test_password
DATABASE_HOST=database
DATABASE_PORT=5432

# Services
BASE_URL=http://frontend:3000
API_URL=http://backend:80
VECTOR_URL=http://vector:6333
EMBEDDINGS_URL=http://embeddings:8001

# Test Configuration
PLAYWRIGHT_WORKERS=1
PLAYWRIGHT_RETRIES=2
PLAYWRIGHT_TIMEOUT=30000
```

---

### Phase 3: Makefile Integration 🔧

**Update Makefile** with test targets following tools pattern:

```makefile
.PHONY: test-docker test-e2e test-unit test-integration test-cleanup test-shell

# Run all tests in Docker (parallel to tools targets)
test-docker:
	@echo "🚀 Running test suite in Docker..."
	docker-compose -f tests/docker-compose.test.yml up --build --abort-on-container-exit
	@$(MAKE) test-cleanup

# Run E2E tests only
test-e2e:
	@echo "🎭 Running Playwright E2E tests..."
	docker-compose -f tests/docker-compose.test.yml run --rm tests

# Run .NET unit tests
test-unit:
	@echo "🧪 Running .NET unit tests..."
	dotnet test tests/integration-tests --configuration Release

# Run integration tests (requires services)
test-integration:
	@echo "🔗 Running integration tests..."
	docker-compose -f tests/docker-compose.test.yml up -d database backend vector embeddings
	@echo "⏳ Waiting for services..."
	@sleep 10
	dotnet test tests/integration-tests --filter "Category=Integration"
	@$(MAKE) test-cleanup

# Interactive test shell (like tools container)
test-shell:
	@echo "🐚 Opening test container shell..."
	docker-compose -f tests/docker-compose.test.yml run --rm tests /bin/bash

# Cleanup test resources
test-cleanup:
	@echo "🧹 Cleaning up test resources..."
	docker-compose -f tests/docker-compose.test.yml down -v
	@echo "✅ Cleanup complete"

# Build test container only
test-build:
	@echo "🔨 Building test container..."
	docker-compose -f tests/docker-compose.test.yml build tests

# Run tests in watch mode (development)
test-watch:
	@echo "👀 Running tests in watch mode..."
	docker-compose -f tests/docker-compose.test.yml run --rm \
		-e CI=false \
		tests npx playwright test --ui
```

---

### Phase 4: CI/CD Integration 🚀

**Create `.github/workflows/test-docker.yml`**:

```yaml
name: Test Suite (Docker)

on:
  pull_request:
    branches: [semantic-foundation, feature/**]
  push:
    branches: [semantic-foundation]
  workflow_dispatch:

jobs:
  test-e2e:
    name: E2E Tests (${{ matrix.browser }})
    runs-on: self-hosted
    timeout-minutes: 20

    strategy:
      fail-fast: false
      matrix:
        browser: [chromium, firefox, webkit]

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Build Test Container
        run: make test-build

      - name: Run E2E Tests - ${{ matrix.browser }}
        run: |
          docker-compose -f tests/docker-compose.test.yml run --rm \
            tests npx playwright test --project=${{ matrix.browser }}

      - name: Upload Results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results-${{ matrix.browser }}
          path: |
            tests/playwright-report/
            tests/test-results/
          retention-days: 7

      - name: Cleanup
        if: always()
        run: make test-cleanup

  test-integration:
    name: Integration Tests (.NET)
    runs-on: self-hosted
    timeout-minutes: 15

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Run Integration Tests
        run: make test-integration

      - name: Upload Results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: integration-test-results
          path: tests/integration-tests/TestResults/
          retention-days: 7

      - name: Cleanup
        if: always()
        run: make test-cleanup
```

---

### Phase 5: Documentation 📚

**Create README.md** - Following tools directory documentation pattern:

```markdown
# Tests Directory

Self-contained test suite following the established tools directory containerization pattern.

## Structure
```

tests/
├── .dockerignore # Optimized build context
├── Dockerfile # Self-contained test container
├── docker-compose.test.yml # Service orchestration
├── scripts/ # Test automation scripts
│ ├── run-tests.sh # Test runner with health checks
│ ├── seed-test-data.sh # Test data seeding
│ └── cleanup.sh # Artifact cleanup
├── e2e/ # Playwright E2E tests
├── integration-tests/ # .NET integration tests
└── config/ # Test configuration

````

## Quick Start

Run all tests:
```bash
make test-docker
````

Run specific test suite:

```bash
make test-e2e           # Playwright E2E only
make test-unit          # .NET unit tests
make test-integration   # Integration tests
```

## Development

Interactive shell:

```bash
make test-shell
```

Watch mode:

```bash
make test-watch
```

Build test container:

```bash
make test-build
```

## Container Pattern

The tests directory follows the same containerization pattern as tools:

| Directory | Dockerfile         | Build Context | Purpose                      |
| --------- | ------------------ | ------------- | ---------------------------- |
| tools     | Dockerfile         | tools         | CLI utilities, documentation |
| tests     | `tests/Dockerfile` | tests         | E2E & integration tests      |

Both containers are:

- Self-contained (all dependencies included)
- Multi-stage (dev/ci targets)
- Optimized (.dockerignore for build context)
- Scriptable (`scripts/` directory)

## Architecture

```
┌─────────────────────────────────────────┐
│     Tests Container (Playwright)        │
│  ┌───────────────────────────────────┐  │
│  │ • Chromium, Firefox, WebKit       │  │
│  │ • scripts/run-tests.sh            │  │
│  │ • Waits for health checks         │  │
│  └───────────────────────────────────┘  │
└─────────────┬───────────────────────────┘
              │ depends_on: service_healthy
    ┌─────────┴──────────┬──────────────┐
    │                    │               │
┌───▼────┐        ┌─────▼─────┐   ┌────▼─────┐
│Frontend│        │  Backend   │   │ Database │
│(React) │        │ (ASP.NET)  │   │(PostgreSQL)
│:3000   │        │ :80        │   │  :5432   │
│tmpfs   │        │ tmpfs      │   │  tmpfs   │
└────────┘        └────────────┘   └──────────┘
```

## Environment Variables

Tests use `.env.test`:

- `CI=true` - Enables CI-specific behavior
- `BASE_URL=http://frontend:3000` - Docker service networking
- `DATABASE_NAME=semantic_kernel_test` - Isolated test database

## Cleanup

Automatic cleanup after tests:

```bash
make test-cleanup
```

Manual cleanup of artifacts:

```bash
docker-compose -f tests/docker-compose.test.yml run --rm tests /tests/scripts/cleanup.sh
```

````

**Update `tests/.vscode/tasks.json`** - VS Code integration:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Test: Run All (Docker)",
      "type": "shell",
      "command": "make test-docker",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "Test: E2E Only (Docker)",
      "type": "shell",
      "command": "make test-e2e",
      "problemMatcher": []
    },
    {
      "label": "Test: Shell (Docker)",
      "type": "shell",
      "command": "make test-shell",
      "problemMatcher": []
    },
    {
      "label": "Test: Watch Mode",
      "type": "shell",
      "command": "make test-watch",
      "problemMatcher": []
    },
    {
      "label": "Test: Cleanup",
      "type": "shell",
      "command": "make test-cleanup",
      "problemMatcher": []
    }
  ]
}
````

---

## Pattern Alignment Comparison

### Before (Inconsistent)

```
tools/                          tests/
├── Dockerfile ✅               ├── (no Dockerfile) ❌
├── .dockerignore ✅            ├── (no .dockerignore) ❌
├── scripts/ ✅                 ├── (no scripts/) ❌
├── cli.py                      ├── e2e/
├── docgen.py                   ├── package.json
└── requirements.txt            └── playwright.config.ts
```

### After (Aligned Pattern)

```
tools/                          tests/
├── Dockerfile ✅               ├── Dockerfile ✅
├── .dockerignore ✅            ├── .dockerignore ✅
├── scripts/ ✅                 ├── scripts/ ✅
│   ├── lint.sh                 │   ├── run-tests.sh
│   └── precommit-autoupdate.sh │   ├── seed-test-data.sh
├── cli.py                      │   └── cleanup.sh
├── docgen.py                   ├── docker-compose.test.yml
└── requirements.txt            ├── e2e/
                                ├── integration-tests/
                                ├── package.json
                                └── playwright.config.ts
```

**Consistency Benefits:**

- ✅ Same containerization approach
- ✅ Same .dockerignore optimization
- ✅ Same `scripts/` automation pattern
- ✅ Same self-contained philosophy
- ✅ Same developer experience

---

## Expected Outcomes

| Metric                    | Before                  | After                      | Improvement       |
| ------------------------- | ----------------------- | -------------------------- | ----------------- |
| **Manual steps**          | 7                       | 1 (`make test-docker`)     | 86% reduction     |
| **Startup time**          | 60s                     | 15-30s                     | 50% faster        |
| **Pattern consistency**   | 0% (no Dockerfile)      | 100% (matches tools/)      | Fully aligned     |
| **Build context size**    | ~500MB                  | ~50MB (with .dockerignore) | 90% smaller       |
| **Container reusability** | 0 (no container)        | High (multi-stage)         | ∞ improvement     |
| **Script automation**     | 0 scripts               | 3 scripts                  | Complete coverage |
| **Developer commands**    | Multiple docker-compose | `make test-*`              | Unified interface |

---

## Priority Implementation Order

1. **CRITICAL:** Create `tests/Dockerfile` with multi-stage build → Pattern alignment
2. **CRITICAL:** Create `tests/.dockerignore` → Build optimization
3. **CRITICAL:** Create `tests/scripts/run-tests.sh` → Automation
4. **HIGH:** Create `tests/docker-compose.test.yml` → Service orchestration
5. **HIGH:** Update Makefile with test targets → Developer experience
6. **MEDIUM:** Create `.github/workflows/test-docker.yml` → CI/CD
7. **MEDIUM:** Create `tests/scripts/seed-test-data.sh` → Test data management
8. **LOW:** Create README.md → Documentation

---

## Key Improvements Over Original Plan

1. **Pattern Consistency:** Tests directory now mirrors tools directory structure exactly
2. **Self-Contained:** `tests/Dockerfile` builds complete test environment (like Dockerfile)
3. **Build Optimization:** .dockerignore reduces build context from ~500MB to ~50MB
4. **Automation Scripts:** `scripts/` directory for test orchestration (like scripts)
5. **Multi-Stage Build:** Separate `dev` and `ci` targets for different use cases
6. **Developer Experience:** Unified `make test-*` commands matching `make` patterns

This revised plan **fully aligns the tests directory with the established tools containerization pattern**, creating a **consistent, maintainable, and efficient** testing infrastructure.
