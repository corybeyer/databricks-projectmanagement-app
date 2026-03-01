#!/bin/bash
# Block direct commits to develop and main branches.
# Allows commits only on feature/*, bugfix/*, hotfix/* branches.
# No external dependencies. Portable across Git Bash / Linux / macOS.
INPUT=$(cat)

# Extract the actual command from the JSON tool input, then check for git commit.
# Grepping the full JSON blob is too broad — descriptions and context also contain
# the word "commit", causing false positives on git stash, git status, etc.
COMMAND=$(echo "$INPUT" | /c/Users/coryb/anaconda3/python.exe -c "import sys,json; print(json.load(sys.stdin).get('input',''))" 2>/dev/null)

if ! echo "$COMMAND" | grep -q 'git commit'; then
  exit 0
fi

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

if [[ "$BRANCH" == "main" || "$BRANCH" == "develop" ]]; then
  echo "Blocked: Cannot commit directly to '$BRANCH'. Use /start-feature to create a feature branch first." >&2
  exit 2
fi

exit 0
