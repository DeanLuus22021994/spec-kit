#!/usr/bin/env bash
set -euo pipefail

# Script to auto-update pre-commit hooks with `pre-commit autoupdate` and create a PR
# Ensure you have `gh` installed and authenticated (for PR creation)

echo "Running pre-commit autoupdate..."
pre-commit autoupdate

if [ -n "$(git status --porcelain)" ]; then
  git add .pre-commit-config.yaml
  git commit -m "chore(pre-commit): autoupdate hooks"
  git push origin HEAD
  if command -v gh >/dev/null 2>&1; then
    echo "Creating pull request via gh CLI..."
    gh pr create --title "chore(pre-commit): autoupdate hooks" --body "Automated pre-commit autoupdate" --base semantic-foundation --head "$(git rev-parse --abbrev-ref HEAD)" || true
  else
    echo "gh CLI not found; please create a PR manually from your branch"
  fi
else
  echo "No changes after autoupdate"
fi

echo "Auto-update completed."
