#!/bin/bash
# Validate that git commit messages follow conventional commit format.
# Valid types: feat, fix, refactor, schema, style, docs, test, deploy, chore
INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only check git commit commands that have a -m flag
if ! echo "$CMD" | grep -qE '^\s*git\s+commit.*-m'; then
  exit 0
fi

# Extract the commit message — handle both -m "msg" and heredoc patterns
MSG=$(echo "$CMD" | grep -oP '(?<=-m\s")[^"]*' | head -1)

# If no simple -m "msg" match, allow it through (heredoc or complex format)
if [[ -z "$MSG" ]]; then
  exit 0
fi

# Check conventional commit format
if ! echo "$MSG" | grep -qE '^(feat|fix|refactor|schema|style|docs|test|deploy|chore):'; then
  echo "Blocked: Commit message must start with a valid type (feat|fix|refactor|schema|style|docs|test|deploy|chore). Got: '$MSG'" >&2
  exit 2
fi

exit 0
