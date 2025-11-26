#!/bin/bash
#
# validate-pr.sh
# Run validation on changed files in PR
#

set -e

# Configuration
PROFILE="${VALIDATION_PROFILE:-recommended}"
BASE_BRANCH="${BASE_BRANCH:-main}"
OUTPUT_DIR="${OUTPUT_DIR:-./validation-results}"

echo "========================================"
echo "PR VALIDATION"
echo "========================================"
echo "Profile: $PROFILE"
echo "Base Branch: $BASE_BRANCH"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Get list of changed YAML files
echo "Detecting changed files..."
CHANGED_FILES=$(git diff --name-only origin/$BASE_BRANCH...HEAD | grep -E '\.(yaml|yml)$' || true)

if [ -z "$CHANGED_FILES" ]; then
    echo "No YAML files changed in this PR"
    exit 0
fi

echo "Changed YAML files:"
echo "$CHANGED_FILES" | while read -r file; do
    echo "  - $file"
done
echo ""

# Run validation on each changed file
TOTAL_FILES=0
PASSED_FILES=0
FAILED_FILES=0
ERROR_COUNT=0
WARNING_COUNT=0

while IFS= read -r file; do
    if [ ! -f "$file" ]; then
        echo "⚠️  File deleted: $file (skipping)"
        continue
    fi

    TOTAL_FILES=$((TOTAL_FILES + 1))
    echo "Validating: $file"

    # Run validation
    if python -m core.cli validate --mode "$PROFILE" --format json --input "$file" > "$OUTPUT_DIR/$(basename "$file").json" 2>&1; then
        echo "  ✓ Passed"
        PASSED_FILES=$((PASSED_FILES + 1))
    else
        echo "  ✗ Failed"
        FAILED_FILES=$((FAILED_FILES + 1))

        # Parse results if JSON output exists
        RESULT_FILE="$OUTPUT_DIR/$(basename "$file").json"
        if [ -f "$RESULT_FILE" ]; then
            FILE_ERRORS=$(jq -r '.errors // 0' "$RESULT_FILE" 2>/dev/null || echo "0")
            FILE_WARNINGS=$(jq -r '.warnings // 0' "$RESULT_FILE" 2>/dev/null || echo "0")
            ERROR_COUNT=$((ERROR_COUNT + FILE_ERRORS))
            WARNING_COUNT=$((WARNING_COUNT + FILE_WARNINGS))
        fi
    fi
done <<< "$CHANGED_FILES"

echo ""
echo "========================================"
echo "VALIDATION SUMMARY"
echo "========================================"
echo "Files: $TOTAL_FILES"
echo "Passed: $PASSED_FILES"
echo "Failed: $FAILED_FILES"
echo "Errors: $ERROR_COUNT"
echo "Warnings: $WARNING_COUNT"
echo ""

# Generate PR comment
COMMENT_FILE="$OUTPUT_DIR/pr-comment.md"
cat > "$COMMENT_FILE" << EOF
## YAML Validation Results

| Metric | Value |
|--------|-------|
| Files Checked | $TOTAL_FILES |
| Passed | $PASSED_FILES ✓ |
| Failed | $FAILED_FILES ✗ |
| Errors | $ERROR_COUNT |
| Warnings | $WARNING_COUNT |

**Profile:** \`$PROFILE\`

EOF

if [ $FAILED_FILES -gt 0 ]; then
    echo "### Failed Files" >> "$COMMENT_FILE"
    echo "" >> "$COMMENT_FILE"
    while IFS= read -r file; do
        RESULT_FILE="$OUTPUT_DIR/$(basename "$file").json"
        if [ -f "$RESULT_FILE" ]; then
            echo "- \`$file\`" >> "$COMMENT_FILE"

            # Extract first few violations
            jq -r '.violations[:3] | .[] | "  - **" + .ruleId + "**: " + .message' "$RESULT_FILE" 2>/dev/null >> "$COMMENT_FILE" || true
        fi
    done <<< "$CHANGED_FILES"
fi

echo "PR comment generated: $COMMENT_FILE"

# Post comment if GitHub CLI is available
if command -v gh &> /dev/null; then
    if [ -n "$GITHUB_REF" ]; then
        PR_NUMBER=$(echo "$GITHUB_REF" | grep -oP 'refs/pull/\K\d+' || echo "")
        if [ -n "$PR_NUMBER" ]; then
            echo "Posting comment to PR #$PR_NUMBER..."
            gh pr comment "$PR_NUMBER" --body-file "$COMMENT_FILE" || echo "Failed to post comment"
        fi
    fi
fi

# Exit with error if validation failed
if [ $FAILED_FILES -gt 0 ]; then
    echo ""
    echo "❌ Validation failed"
    exit 1
else
    echo "✅ All files passed validation"
    exit 0
fi
