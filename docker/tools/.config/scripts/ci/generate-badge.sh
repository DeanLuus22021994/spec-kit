#!/bin/bash
#
# generate-badge.sh
# Generate validation status badges
#

set -e

# Configuration
OUTPUT_DIR="${OUTPUT_DIR:-./badges}"
RESULTS_FILE="${RESULTS_FILE:-./validation-results/summary.json}"

echo "Generating validation badges..."

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check if results file exists
if [ ! -f "$RESULTS_FILE" ]; then
    echo "Results file not found: $RESULTS_FILE"
    echo "Generating default badge..."

    # Create default unknown badge
    cat > "$OUTPUT_DIR/validation-badge.svg" << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" width="120" height="20">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <mask id="a">
    <rect width="120" height="20" rx="3" fill="#fff"/>
  </mask>
  <g mask="url(#a)">
    <path fill="#555" d="M0 0h65v20H0z"/>
    <path fill="#9f9f9f" d="M65 0h55v20H65z"/>
    <path fill="url(#b)" d="M0 0h120v20H0z"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="32.5" y="15" fill="#010101" fill-opacity=".3">validation</text>
    <text x="32.5" y="14">validation</text>
    <text x="91.5" y="15" fill="#010101" fill-opacity=".3">unknown</text>
    <text x="91.5" y="14">unknown</text>
  </g>
</svg>
EOF
    exit 0
fi

# Parse results
PASSED=$(jq -r '.passed // 0' "$RESULTS_FILE")
FAILED=$(jq -r '.failed // 0' "$RESULTS_FILE")
TOTAL=$(jq -r '.total // 0' "$RESULTS_FILE")
ERRORS=$(jq -r '.errors // 0' "$RESULTS_FILE")
WARNINGS=$(jq -r '.warnings // 0' "$RESULTS_FILE")

# Calculate pass rate
if [ "$TOTAL" -gt 0 ]; then
    PASS_RATE=$(echo "scale=1; $PASSED * 100 / $TOTAL" | bc)
else
    PASS_RATE=0
fi

# Determine badge color
if [ "$ERRORS" -gt 0 ]; then
    COLOR="#e05d44"  # Red
    STATUS="failing"
elif [ "$WARNINGS" -gt 0 ]; then
    COLOR="#dfb317"  # Yellow
    STATUS="warning"
elif [ "$PASSED" -eq "$TOTAL" ]; then
    COLOR="#97ca00"  # Green
    STATUS="passing"
else
    COLOR="#9f9f9f"  # Gray
    STATUS="unknown"
fi

echo "Status: $STATUS ($PASS_RATE% pass rate)"
echo "Errors: $ERRORS, Warnings: $WARNINGS"

# Generate validation status badge
cat > "$OUTPUT_DIR/validation-status.svg" << EOF
<svg xmlns="http://www.w3.org/2000/svg" width="120" height="20">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <mask id="a">
    <rect width="120" height="20" rx="3" fill="#fff"/>
  </mask>
  <g mask="url(#a)">
    <path fill="#555" d="M0 0h65v20H0z"/>
    <path fill="$COLOR" d="M65 0h55v20H65z"/>
    <path fill="url(#b)" d="M0 0h120v20H0z"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="32.5" y="15" fill="#010101" fill-opacity=".3">validation</text>
    <text x="32.5" y="14">validation</text>
    <text x="91.5" y="15" fill="#010101" fill-opacity=".3">$STATUS</text>
    <text x="91.5" y="14">$STATUS</text>
  </g>
</svg>
EOF

# Generate coverage badge
COVERAGE_PERCENT=$(jq -r '.coverage.coverage_percent // 0' "$RESULTS_FILE" 2>/dev/null || echo "0")

if (( $(echo "$COVERAGE_PERCENT >= 80" | bc -l) )); then
    COVERAGE_COLOR="#97ca00"  # Green
elif (( $(echo "$COVERAGE_PERCENT >= 60" | bc -l) )); then
    COVERAGE_COLOR="#dfb317"  # Yellow
else
    COVERAGE_COLOR="#e05d44"  # Red
fi

cat > "$OUTPUT_DIR/coverage-badge.svg" << EOF
<svg xmlns="http://www.w3.org/2000/svg" width="110" height="20">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <mask id="a">
    <rect width="110" height="20" rx="3" fill="#fff"/>
  </mask>
  <g mask="url(#a)">
    <path fill="#555" d="M0 0h60v20H0z"/>
    <path fill="$COVERAGE_COLOR" d="M60 0h50v20H60z"/>
    <path fill="url(#b)" d="M0 0h110v20H0z"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="30" y="15" fill="#010101" fill-opacity=".3">coverage</text>
    <text x="30" y="14">coverage</text>
    <text x="84" y="15" fill="#010101" fill-opacity=".3">${COVERAGE_PERCENT}%</text>
    <text x="84" y="14">${COVERAGE_PERCENT}%</text>
  </g>
</svg>
EOF

echo "✓ Generated: $OUTPUT_DIR/validation-status.svg"
echo "✓ Generated: $OUTPUT_DIR/coverage-badge.svg"

# Generate markdown with badges
cat > "$OUTPUT_DIR/badges.md" << EOF
# Validation Badges

![Validation Status](./$OUTPUT_DIR/validation-status.svg)
![Coverage](./$OUTPUT_DIR/coverage-badge.svg)

## Current Status

- **Status:** $STATUS
- **Pass Rate:** $PASS_RATE%
- **Coverage:** $COVERAGE_PERCENT%
- **Errors:** $ERRORS
- **Warnings:** $WARNINGS
- **Total Files:** $TOTAL
EOF

echo "✓ Generated: $OUTPUT_DIR/badges.md"
echo ""
echo "Badges generated successfully!"
