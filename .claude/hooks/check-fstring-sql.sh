#!/bin/bash
# check-fstring-sql.sh — Warn (non-blocking) when f-string SQL is detected in staged files
# Hook type: PreToolUse (advisory only — exits 0 always)

# Only check on git commit commands
INPUT=$(cat /dev/stdin 2>/dev/null || echo "")
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)

# Only run on git commit commands
if [ "$TOOL_NAME" != "Bash" ]; then
    exit 0
fi

if ! echo "$COMMAND" | grep -q "git commit"; then
    exit 0
fi

# Check staged Python files for f-string SQL patterns
STAGED_PY=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null | grep '\.py$')

if [ -z "$STAGED_PY" ]; then
    exit 0
fi

WARNINGS=""
for file in $STAGED_PY; do
    if [ -f "$file" ]; then
        # Look for f-string SQL patterns
        MATCHES=$(grep -n "f['\"].*\(SELECT\|INSERT\|UPDATE\|DELETE\).*{" "$file" 2>/dev/null)
        if [ -n "$MATCHES" ]; then
            WARNINGS="$WARNINGS\n  $file:\n$MATCHES"
        fi
        # Also check for f-string with quoted variables in SQL context
        MATCHES2=$(grep -n "'{[a-zA-Z_]*}'" "$file" 2>/dev/null)
        if [ -n "$MATCHES2" ]; then
            WARNINGS="$WARNINGS\n  $file:\n$MATCHES2"
        fi
    fi
done

if [ -n "$WARNINGS" ]; then
    echo "" >&2
    echo "WARNING: F-string SQL detected in staged files:" >&2
    echo -e "$WARNINGS" >&2
    echo "" >&2
    echo "Consider migrating to parameterized queries (see /review-databricks)." >&2
    echo "This is a WARNING — commit will proceed." >&2
    echo "" >&2
fi

# Always exit 0 — this is advisory, not blocking
exit 0
