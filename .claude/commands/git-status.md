---
description: Summarize Git repository status
allowed-tools: Bash(git *)
---

Run the following git commands and summarize the results:

1. `git branch --show-current` — get the current branch name
2. `git status --short` — show uncommitted changes
3. `git log --oneline -5` — show 5 most recent commits
4. `git rev-list --left-right --count @{upstream}...HEAD 2>/dev/null || echo "no upstream"` — ahead/behind remote

Present a clean summary with:
- Current branch name
- Uncommitted changes (or "working tree clean")
- Recent commits
- Ahead/behind remote status
- Suggested next actions
- Any warnings or issues
