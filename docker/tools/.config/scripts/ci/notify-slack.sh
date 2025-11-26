#!/bin/bash
#
# notify-slack.sh
# Send validation results to Slack
#

set -e

# Configuration
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
RESULTS_FILE="${RESULTS_FILE:-./validation-results/summary.json}"
BUILD_URL="${BUILD_URL:-}"
COMMIT_SHA="${COMMIT_SHA:-$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')}"
BRANCH="${BRANCH:-$(git branch --show-current 2>/dev/null || echo 'unknown')}"

if [ -z "$SLACK_WEBHOOK_URL" ]; then
    echo "Error: SLACK_WEBHOOK_URL environment variable not set"
    echo "Skipping Slack notification"
    exit 0
fi

if [ ! -f "$RESULTS_FILE" ]; then
    echo "Error: Results file not found: $RESULTS_FILE"
    exit 1
fi

echo "Sending validation results to Slack..."

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

# Determine status
if [ "$ERRORS" -gt 0 ]; then
    STATUS="❌ Failed"
    COLOR="#e05d44"
elif [ "$WARNINGS" -gt 0 ]; then
    STATUS="⚠️  Warning"
    COLOR="#dfb317"
elif [ "$PASSED" -eq "$TOTAL" ]; then
    STATUS="✅ Passed"
    COLOR="#97ca00"
else
    STATUS="❓ Unknown"
    COLOR="#9f9f9f"
fi

# Build message
MESSAGE="YAML Validation: $STATUS"

# Build blocks for detailed message
BLOCKS=$(cat <<EOF
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "YAML Validation Results",
        "emoji": true
      }
    },
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*Status:*\n$STATUS"
        },
        {
          "type": "mrkdwn",
          "text": "*Pass Rate:*\n$PASS_RATE%"
        },
        {
          "type": "mrkdwn",
          "text": "*Branch:*\n\`$BRANCH\`"
        },
        {
          "type": "mrkdwn",
          "text": "*Commit:*\n\`$COMMIT_SHA\`"
        }
      ]
    },
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*Total Files:*\n$TOTAL"
        },
        {
          "type": "mrkdwn",
          "text": "*Passed:*\n$PASSED ✓"
        },
        {
          "type": "mrkdwn",
          "text": "*Errors:*\n$ERRORS"
        },
        {
          "type": "mrkdwn",
          "text": "*Warnings:*\n$WARNINGS"
        }
      ]
    }
EOF
)

# Add build URL if available
if [ -n "$BUILD_URL" ]; then
    BLOCKS="$BLOCKS"$(cat <<EOF
,
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "<$BUILD_URL|View Build Details>"
      }
    }
EOF
)
fi

# Close blocks
BLOCKS="$BLOCKS"$(cat <<EOF
  ]
}
EOF
)

# Send to Slack
HTTP_CODE=$(curl -X POST \
  -H 'Content-Type: application/json' \
  -d "$BLOCKS" \
  -w "%{http_code}" \
  -o /tmp/slack-response.txt \
  "$SLACK_WEBHOOK_URL")

if [ "$HTTP_CODE" -eq 200 ]; then
    echo "✓ Slack notification sent successfully"
else
    echo "✗ Failed to send Slack notification (HTTP $HTTP_CODE)"
    cat /tmp/slack-response.txt
    exit 1
fi

rm -f /tmp/slack-response.txt
