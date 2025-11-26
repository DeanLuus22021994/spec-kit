#!/usr/bin/env bash
set -euo pipefail

# Create reports directory
mkdir -p reports

echo "Running pylint..."
python -m pylint --rcfile=.pylintrc --output-format=text --jobs=4 tools src tests | tee reports/pylint_report.txt

echo "Pylint complete. Report saved to reports/pylint_report.txt"

echo "Running pre-commit hooks (formatters and other hooks)..."
pre-commit run --all-files || true
echo "Pre-commit checks complete" || true

if command -v sqlfluff >/dev/null 2>&1; then
	echo "Running sqlfluff lint (if available)..."
	sqlfluff lint infrastructure/database || true
fi
