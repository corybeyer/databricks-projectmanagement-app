#!/bin/bash
# Warn if there are uncommitted changes at session end.
# No jq dependency — doesn't need to parse input.
CHANGES=$(git status --porcelain 2>/dev/null)

if [[ -n "$CHANGES" ]]; then
  echo "WARNING: You have uncommitted changes:" >&2
  echo "$CHANGES" >&2
  echo "" >&2
  echo "Use /commit to save your work before ending the session." >&2
fi

exit 0
