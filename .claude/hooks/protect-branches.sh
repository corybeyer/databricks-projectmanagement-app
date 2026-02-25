#!/bin/bash
# Block direct commits to develop and main branches.
# Allows commits only on feature/*, bugfix/*, hotfix/* branches.
# No external dependencies. Portable across Git Bash / Linux / macOS.
INPUT=$(cat)

# Check if this is a git commit command (search the raw JSON)
if ! echo "$INPUT" | grep -q 'git commit\|git.*commit'; then
  exit 0
fi

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

if [[ "$BRANCH" == "main" || "$BRANCH" == "develop" ]]; then
  echo "Blocked: Cannot commit directly to '$BRANCH'. Use /start-feature to create a feature branch first." >&2
  exit 2
fi

exit 0
