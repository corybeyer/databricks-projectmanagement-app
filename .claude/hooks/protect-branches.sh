#!/bin/bash
# Block direct commits to develop and main branches.
# Allows commits only on feature/*, bugfix/*, hotfix/* branches.
INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only check git commit commands
if ! echo "$CMD" | grep -qE '^\s*git\s+commit'; then
  exit 0
fi

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

if [[ "$BRANCH" == "main" || "$BRANCH" == "develop" ]]; then
  echo "Blocked: Cannot commit directly to '$BRANCH'. Use /start-feature to create a feature branch first." >&2
  exit 2
fi

exit 0
