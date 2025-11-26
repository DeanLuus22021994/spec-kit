#!/bin/bash
# Pattern Validation Script
# Validates .config/ pattern consistency across the codebase

set -e

echo "=== .config/ Pattern Validation ==="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

violations=0
warnings=0

# 1. Check Copilot Context Files
echo "1. Validating Copilot Context Files..."
config_dirs=$(find . -type d -name ".config" -not -path "*/node_modules/*" -not -path "*/.git/*")

if [ -z "$config_dirs" ]; then
    echo -e "${RED}❌ No .config directories found${NC}"
    exit 1
fi

missing_index=()
for dir in $config_dirs; do
    index_file="$dir/copilot/index.yml"
    if [ ! -f "$index_file" ]; then
        missing_index+=("$dir")
        violations=$((violations + 1))
    else
        line_count=$(wc -l < "$index_file")
        if [ "$line_count" -lt 50 ]; then
            echo -e "${YELLOW}⚠️  $index_file has only $line_count lines (minimum 50 recommended)${NC}"
            warnings=$((warnings + 1))
        else
            echo -e "${GREEN}✅ $index_file ($line_count lines)${NC}"
        fi
    fi
done

if [ ${#missing_index[@]} -gt 0 ]; then
    echo -e "${RED}❌ Missing copilot/index.yml in:${NC}"
    printf '%s\n' "${missing_index[@]}"
fi

# 2. Check Pollution Prevention
echo ""
echo "2. Validating Pollution Prevention..."

# Python pollution
if find . -type d -name "__pycache__" -not -path "*/node_modules/*" 2>/dev/null | grep -q .; then
    echo -e "${RED}❌ Found __pycache__ directories (should be .gitignored)${NC}"
    violations=$((violations + 1))
fi

if find . -type d -name ".pytest_cache" 2>/dev/null | grep -q .; then
    echo -e "${RED}❌ Found .pytest_cache directories (should be .gitignored)${NC}"
    violations=$((violations + 1))
fi

if find . -type d -name ".mypy_cache" 2>/dev/null | grep -q .; then
    echo -e "${RED}❌ Found .mypy_cache directories (should be .gitignored)${NC}"
    violations=$((violations + 1))
fi

if [ $violations -eq 0 ]; then
    echo -e "${GREEN}✅ No codebase pollution detected${NC}"
fi

# 3. Check Docker Best Practices
echo ""
echo "3. Validating Docker Best Practices..."

dockerfiles=$(find . -name "Dockerfile" -not -path "*/node_modules/*")
docker_violations=0

for dockerfile in $dockerfiles; do
    # Check for non-root user
    if ! grep -q "USER.*[^root]" "$dockerfile"; then
        echo -e "${YELLOW}⚠️  $dockerfile may not use non-root user${NC}"
        warnings=$((warnings + 1))
    fi

    # Check for runtime dependency install (anti-pattern)
    if grep -q "CMD.*pip install" "$dockerfile" || grep -q "CMD.*npm install" "$dockerfile"; then
        echo -e "${RED}❌ $dockerfile has runtime dependency install (should be baked in RUN)${NC}"
        docker_violations=$((docker_violations + 1))
        violations=$((violations + 1))
    fi
done

if [ $docker_violations -eq 0 ]; then
    echo -e "${GREEN}✅ Docker best practices validated${NC}"
fi

# 4. Pattern Adoption Report
echo ""
echo "4. Pattern Adoption Report..."

total_dirs=9
config_count=$(find . -type d -name ".config" -not -path "*/node_modules/*" -not -path "*/.git/*" | wc -l)
adoption_pct=$((config_count * 100 / total_dirs))

echo "Adoption: $config_count/$total_dirs directories ($adoption_pct%)"
echo ""
echo "Directories with .config/:"
find . -type d -name ".config" -not -path "*/node_modules/*" -not -path "*/.git/*" | sort
echo ""

if [ $adoption_pct -lt 100 ]; then
    echo -e "${YELLOW}⚠️  Pattern not yet fully adopted (target: 100%)${NC}"
    warnings=$((warnings + 1))
else
    echo -e "${GREEN}✅ Pattern fully adopted across all directories${NC}"
fi

# 5. Documentation Standards Check
echo ""
echo "5. Documentation Standards Check..."

scattered_docs=$(find . -path "*/.config/documentation/*.md" -not -path "*/.git/*" 2>/dev/null)
if [ -n "$scattered_docs" ]; then
    echo -e "${RED}❌ Found scattered documentation in .config/documentation/${NC}"
    echo "$scattered_docs" | while read -r file; do
        echo -e "  ${RED}→ $file${NC}"
    done
    echo -e "${YELLOW}  Fix: Move to docs/ root per .github/DOCUMENTATION_STANDARDS.md${NC}"
    violations=$((violations + 1))
else
    echo -e "${GREEN}✅ No scattered documentation (centralized docs/ compliance)${NC}"
fi

# Summary
echo ""
echo "=== Summary ==="
if [ $violations -gt 0 ]; then
    echo -e "${RED}❌ Found $violations violations${NC}"
fi

if [ $warnings -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Found $warnings warnings${NC}"
fi

if [ $violations -eq 0 ] && [ $warnings -eq 0 ]; then
    echo -e "${GREEN}✅ All validations passed${NC}"
fi

echo ""
echo "For more details, see: docs/development/config-pattern-guide.md"

exit $violations
