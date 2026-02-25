#!/bin/bash
# Validate that git commit messages follow conventional commit format.
# Valid types: feat, fix, refactor, schema, style, docs, test, deploy, chore
# No external dependencies. Portable across Git Bash / Linux / macOS.
INPUT=$(cat)

# Only check git commit commands that have a -m flag
if ! echo "$INPUT" | grep -q 'git commit.*-m'; then
  exit 0
fi

# Allow heredoc-style commits through (they use cat <<'EOF' pattern)
if echo "$INPUT" | grep -q 'EOF'; then
  exit 0
fi

# Extract message: handle both escaped \" and regular " in JSON
# Pattern: -m "message" or -m \"message\"
MSG=$(echo "$INPUT" | sed 's/\\"/"/g' | sed -n 's/.*-m\s*"\([^"]*\)".*/\1/p' | head -1)

# If we can't extract a message, allow through (complex format)
if [[ -z "$MSG" ]]; then
  exit 0
fi

# Check conventional commit format
if ! echo "$MSG" | grep -qE '^(feat|fix|refactor|schema|style|docs|test|deploy|chore):'; then
  echo "Blocked: Commit message must start with a valid type (feat|fix|refactor|schema|style|docs|test|deploy|chore). Got: '$MSG'" >&2
  exit 2
fi

exit 0
