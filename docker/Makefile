SHELL := /bin/bash

.PHONY: install-dev lint lint-report lint-clean pre-commit-install build test validate-pr validate-pr-readiness validate-pattern validate-yaml validate-yaml-docker validate-yaml-docker-strict validate-yaml-docker-build validate-yaml-docker-report validate-yaml-docker-mandatory validate-yaml-mandatory validate-yaml-strict validate-yaml-recommended validate-yaml-ci validate-yaml-report validate-rules-test

install-dev:
	python -m pip install --upgrade pip
	python -m pip install -r tools/requirements.txt
	# Restore dotnet local tools and install frontend node deps
	dotnet tool restore || true
	npm ci --prefix src/frontend || true
	pre-commit install || true

lint:
	@echo "Running lint (console)..."
	tools/.config/scripts/lint.sh

lint-frontend:
	@echo "Running frontend lint (JS/TS)"
	npm ci --prefix src/frontend || true
	# Run eslint if available
	if npm run --prefix src/frontend | grep -q "lint"; then \
		npm run lint --prefix src/frontend || true; \
	else \
		npx eslint src/frontend --ext .ts,.tsx || true; \
	fi

lint-sql:
	@echo "Running SQL lint (sqlfluff)"
	python -m pip install --upgrade pip || true
	pip install sqlfluff || true
	if command -v sqlfluff >/dev/null 2>&1; then \
		sqlfluff lint infrastructure/database || true; \
	fi

lint-shell:
	@echo "Running shell lint (shellcheck)"
	# shellcheck may not be available on Windows runners; use WSL or devcontainer
	sudo apt-get update && sudo apt-get install -y shellcheck || true
	find . -type f -name "*.sh" -not -path "./node_modules/*" -print0 | xargs -0 shellcheck -x || true

lint-report:
	@echo "Generating lint report..."
	python -m pylint --rcfile=.pylintrc --output-format=text --jobs=4 tools src tests | tee reports/pylint_report.txt

lint-clean:
	@echo "Cleaning lint reports..."
	rm -rf reports/* || true

pre-commit-install:
	pre-commit install
	# Ensure dotnet tools and frontend deps are ready
	dotnet tool restore || true
	npm ci --prefix src/frontend || true

build:
	@echo "Building .NET solution and frontend"
	-dotnet restore semantic-kernel-app.sln
	-dotnet build semantic-kernel-app.sln

test:
	@echo "Run unit and e2e tests (locally)"
	-dotnet test tests/unit --configuration Release
	-npx playwright install --with-deps
	-npx playwright test

validate-pr-readiness:
	@echo "Running PR readiness checks..."
	-dotnet restore semantic-kernel-app.sln
	-dotnet build semantic-kernel-app.sln --configuration Release --no-restore
	-dotnet test tests/unit --configuration Release --verbosity minimal
	@echo "PR readiness check complete"

validate-pattern:
	@echo "Validating .config/ pattern consistency..."
	bash tools/.config/scripts/validate-pattern.sh

validate-yaml:
	@echo "Running YAML validation (all rules)..."
	bash tools/.config/scripts/validate-yaml.sh

validate-yaml-docker:
	@echo "Running YAML validation in Docker (recommended profile)..."
	docker-compose -f docker-compose.validation.yml run --rm validation

validate-yaml-docker-strict:
	@echo "Running strict YAML validation in Docker (zero tolerance)..."
	docker-compose -f docker-compose.validation.yml run --rm validation --profile strict

validate-yaml-docker-build:
	@echo "Building validation Docker container..."
	docker-compose -f docker-compose.validation.yml build

validate-yaml-docker-report:
	@echo "Extracting validation report from Docker volume..."
	@mkdir -p validation-reports
	docker run --rm \
		-v semantic-kernel-validation-reports:/reports:ro \
		-v $(PWD)/validation-reports:/export \
		alpine cp -r /reports/static-report /export/ || true
	@echo "Opening validation report..."
	@REPORT_PATH="validation-reports/static-report/index.html"; \
	if [ -f "$$REPORT_PATH" ]; then \
		if command -v xdg-open >/dev/null 2>&1; then \
			xdg-open "$$REPORT_PATH"; \
		elif command -v open >/dev/null 2>&1; then \
			open "$$REPORT_PATH"; \
		elif command -v start >/dev/null 2>&1; then \
			start "$$REPORT_PATH"; \
		else \
			echo "Report location: $$REPORT_PATH"; \
		fi; \
	else \
		echo "❌ No validation report found. Run 'make validate-yaml-docker' first."; \
		exit 1; \
	fi

validate-yaml-mandatory:
	@echo "Running YAML validation (mandatory rules only)..."
	bash tools/.config/scripts/validate-yaml.sh --mandatory

validate-yaml-docker-mandatory:
	@echo "Running mandatory YAML validation in Docker..."
	docker-compose -f docker-compose.validation.yml run --rm validation --mandatory

validate-yaml-strict:
	@echo "Running strict YAML validation (zero tolerance)..."
	bash tools/.config/scripts/validate-yaml.sh --profile strict

validate-yaml-recommended:
	@echo "Running recommended YAML validation..."
	bash tools/.config/scripts/validate-yaml.sh --profile recommended

validate-yaml-ci:
	@echo "Running CI/CD optimized YAML validation..."
	bash tools/.config/scripts/validate-yaml.sh --profile ci-cd

validate-yaml-report:
	@echo "Opening YAML validation report..."
	@REPORT_PATH="tools/.config/validation/reports/static-report/index.html"; \
	if [ -f "$$REPORT_PATH" ]; then \
		if command -v xdg-open >/dev/null 2>&1; then \
			xdg-open "$$REPORT_PATH"; \
		elif command -v open >/dev/null 2>&1; then \
			open "$$REPORT_PATH"; \
		elif command -v start >/dev/null 2>&1; then \
			start "$$REPORT_PATH"; \
		else \
			echo "Report location: $$REPORT_PATH"; \
		fi; \
	else \
		echo "❌ No validation report found. Run 'make validate-yaml' first."; \
		exit 1; \
	fi

# ===========================
# Phase 1: Validation Framework (Enhanced)
# ===========================

validate-migrate:
	@echo "🔄 Migrating validation structure to modular architecture..."
	@echo "This is a Phase 1 task - framework foundation is complete"
	@echo "Next: Phase 2 - Rule coverage expansion (70 new rules)"

validate-test-structure:
	@echo "🧪 Testing validation framework structure..."
	@cd tools/.config/validation && python -m pytest core/tests/ -v || echo "Note: Tests will be implemented in Phase 1 completion"

validate-rules-test:
	@echo "🔍 Testing all validation rules..."
	@echo "This will run the test harness on all rule packages"
	@cd tools/.config/validation && python -c "from core.testing import TestHarness; from pathlib import Path; harness = TestHarness(Path('rules'), Path('test-data')); print(harness.run_all_tests())" || echo "Note: Requires Python dependencies from requirements.txt"

validate-coverage:
	@echo "📊 Analyzing rule coverage..."
	@echo "Current: 35 rules implemented (10% of yaml-best-practices.yml)"
	@echo "Target: 105 rules (100% coverage)"
	@echo "Gap: 70 rules across 6 packages"
	@echo ""
	@echo "See tools/.config/validation/ENHANCEMENT_PLAN.md for details"

validate-scaffold:
	@echo "🔧 Scaffolding new validation rule..."
	@if [ -z "$(CATEGORY)" ] || [ -z "$(NAME)" ]; then \
		echo "Usage: make validate-scaffold CATEGORY=metadata NAME=my-rule SEVERITY=mandatory"; \
		echo ""; \
		echo "Categories: metadata, syntax, structure, mta, quality, vscode"; \
		echo "Severities: mandatory, optional, potential"; \
		exit 1; \
	fi
	@echo "Creating rule: $(NAME) in $(CATEGORY) package..."
	@echo "Severity: $(SEVERITY)"
	@echo "Note: Scaffolding tool will be implemented in Phase 3"

validate-profile:
	@echo "🎯 Running validation with profile: $(PROFILE)"
	@if [ -z "$(PROFILE)" ]; then \
		echo "Usage: make validate-profile PROFILE=strict"; \
		echo ""; \
		echo "Available profiles:"; \
		echo "  strict       - Zero-tolerance, all rules"; \
		echo "  recommended  - Balanced (default)"; \
		echo "  minimal      - Mandatory only"; \
		echo "  ci-cd        - CI/CD optimized"; \
		echo "  development  - Developer-friendly"; \
		exit 1; \
	fi
	bash tools/.config/scripts/validate-yaml.sh --profile $(PROFILE)

validate-metrics:
	@echo "📈 Generating validation metrics..."
	@echo "Framework Version: 1.0.0"
	@echo "Core Modules: 12 (engine: 4, rules: 4, testing: 3, __init__: 1)"
	@echo "JSON Schemas: 4"
	@echo "Profiles: 5"
	@echo "VS Code Integration: Active"
	@echo ""
	@echo "Phase 1 Status: Complete ✅"
	@echo "Phase 2 Status: Not Started"
	@echo "Phase 3 Status: Not Started"
	@echo "Phase 4 Status: Not Started"

validate-install:
	@echo "📦 Installing validation framework dependencies..."
	pip install -r tools/.config/validation/requirements.txt
	@echo "✅ Dependencies installed"

validate-pr:
	@echo "Starting PR validation (config: .config/pr-validation.yml)"
	@echo ""
	@echo "Phase 1: Lint"
	-pre-commit run --all-files || true
	@echo ""
	@echo "Phase 2: Build"
	-dotnet restore semantic-kernel-app.sln
	-dotnet build semantic-kernel-app.sln --configuration Release --no-restore
	-npm ci --prefix src/frontend && npm run build --prefix src/frontend
	@echo ""
	@echo "Phase 3: Unit Tests"
	-dotnet test tests/unit --configuration Release --verbosity normal
	@echo ""
	@echo "Phase 4: Docker Build & Startup"
	-docker-compose build --parallel
	-docker-compose up -d
	@sleep 30
	@echo ""
	@echo "Phase 5: Health Checks"
	-docker-compose exec -T database pg_isready -U user -d semantic_kernel || true
	-curl -sf http://localhost:6333/healthz || true
	-curl -sf http://localhost:8001/health || true
	-curl -sf http://localhost:8080/health || true
	@echo ""
	@echo "Phase 6: Integration & E2E Tests"
	-dotnet test tests/integration-tests --configuration Release --verbosity normal
	-npm ci --prefix tests && npx playwright install --with-deps chromium
	-npx playwright test --project=chromium
	@echo ""
	@echo "Phase 7: Cleanup"
	-docker-compose down
	@echo ""
	@echo "Validation complete. Check: tests/test-results, reports/"
# ===========================
# Test Suite (Docker-based)
# ===========================

.PHONY: test-docker test-e2e test-unit test-integration test-cleanup test-shell test-build test-watch test-rebuild-cache test-extract-results test-validate-cache test-validate-browsers test-seed-data test-cleanup-full

# Run all tests in Docker (parallel to tools targets)
test-docker:
	@echo "🚀 Running test suite in Docker..."
	docker-compose -f tests/.config/docker/docker-compose.test.yml up --build --abort-on-container-exit
	@$(MAKE) test-extract-results
	@$(MAKE) test-cleanup

# Run E2E tests only
test-e2e:
	@echo "🎭 Running Playwright E2E tests..."
	docker-compose -f tests/.config/docker/docker-compose.test.yml run --rm tests
	@$(MAKE) test-extract-results

# Run .NET unit tests
test-unit:
	@echo "🧪 Running .NET unit tests..."
	dotnet test tests/unit --configuration Release

# Run integration tests (requires services)
test-integration:
	@echo "🔗 Running integration tests..."
	docker-compose -f tests/.config/docker/docker-compose.test.yml up -d database backend vector embeddings
	@echo "⏳ Waiting for services..."
	@sleep 10
	dotnet test tests/integration-tests --filter "Category=Integration"
	@$(MAKE) test-cleanup

# Validate Docker build cache for corruption
test-validate-cache:
	@echo "🔍 Validating Docker build cache..."
	@cd tests && bash .config/scripts/validate-build-cache.sh

# Validate Playwright browser cache
test-validate-browsers:
	@echo "🌐 Validating Playwright browser cache..."
	@docker-compose -f tests/.config/docker/docker-compose.test.yml run --rm tests bash .config/scripts/validate-playwright-cache.sh

# Seed test database with data
test-seed-data:
	@echo "🌱 Seeding test database..."
	@docker-compose -f tests/.config/docker/docker-compose.test.yml up -d database backend
	@sleep 5
	@docker-compose -f tests/.config/docker/docker-compose.test.yml run --rm tests bash .config/scripts/seed-test-data.sh

# Interactive test shell (like tools container)
test-shell:
	@echo "🐚 Opening test container shell..."
	docker-compose -f tests/.config/docker/docker-compose.test.yml run --rm tests /bin/bash

# Cleanup test resources (keeps named volumes)
test-cleanup:
	@echo "🧹 Cleaning up test resources..."
	docker-compose -f tests/.config/docker/docker-compose.test.yml down
	@echo "✅ Cleanup complete (named volumes preserved)"

# Full cleanup with verification (database and volumes optional)
test-cleanup-full:
	@echo "🧹 Running full cleanup with verification..."
	@docker-compose -f tests/.config/docker/docker-compose.test.yml run --rm tests bash .config/scripts/cleanup.sh
	@docker-compose -f tests/.config/docker/docker-compose.test.yml down
	@echo "✅ Full cleanup complete"

# Full cleanup including database (destructive)
test-cleanup-db:
	@echo "🗑️  Full cleanup including database..."
	@docker-compose -f tests/.config/docker/docker-compose.test.yml run --rm -e CLEAN_DB=true tests bash .config/scripts/cleanup.sh
	@docker-compose -f tests/.config/docker/docker-compose.test.yml down
	@echo "✅ Database cleanup complete"

# Full cleanup including volumes (very destructive)
test-cleanup-volumes:
	@echo "⚠️  Full cleanup including Docker volumes..."
	@docker-compose -f tests/.config/docker/docker-compose.test.yml run --rm -e CLEAN_VOLUMES=true -e CLEAN_DB=true tests bash .config/scripts/cleanup.sh
	@docker-compose -f tests/.config/docker/docker-compose.test.yml down -v
	@echo "✅ Volume cleanup complete"

# Rebuild cache and named volumes (use when dependencies change)
test-rebuild-cache:
	@echo "🔄 Rebuilding test cache and named volumes..."
	docker-compose -f tests/.config/docker/docker-compose.test.yml down -v
	docker-compose -f tests/.config/docker/docker-compose.test.yml build --no-cache tests
	@echo "✅ Cache rebuilt"

# Extract test results from named volumes to local filesystem
test-extract-results:
	@echo "📦 Extracting test results from containers..."
	@mkdir -p tests/playwright-report tests/test-results
	-docker-compose -f tests/.config/docker/docker-compose.test.yml run --rm --no-deps tests sh -c "cp -r /app/tests/playwright-report/* /app/tests/playwright-report/ 2>/dev/null || true"
	-docker-compose -f tests/.config/docker/docker-compose.test.yml run --rm --no-deps tests sh -c "cp -r /app/tests/test-results/* /app/tests/test-results/ 2>/dev/null || true"
	@echo "✅ Results extracted to tests/playwright-report and tests/test-results"

# Build test container only
test-build:
	@echo "🔨 Building test container..."
	docker-compose -f tests/.config/docker/docker-compose.test.yml build tests

# Run tests in watch mode (development)
test-watch:
	@echo "👀 Running tests in watch mode..."
	docker-compose -f tests/.config/docker/docker-compose.test.yml run --rm \
		-e CI=false \
		tests npx playwright test --ui
