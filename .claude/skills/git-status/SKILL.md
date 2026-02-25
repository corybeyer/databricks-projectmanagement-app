---
name: git-status
description: Show current git status — branch, uncommitted changes, ahead/behind remote
argument-hint: ""
---

Show the user a clear summary of where they are in git. Run these commands and present the results in a clean format:

1. Run `git rev-parse --abbrev-ref HEAD` to get the current branch name
2. Run `git status --short` to show uncommitted changes
3. Run `git log --oneline -5` to show recent commits
4. Run `git rev-list --left-right --count origin/$(git rev-parse --abbrev-ref HEAD)...HEAD 2>/dev/null` to check ahead/behind (if remote tracking exists)

Present the output as:

```
Branch: <branch-name>
Remote: <ahead/behind status or "no remote tracking">

Recent commits:
  <last 5 commits>

Uncommitted changes:
  <changes or "Clean working tree">
```

Keep it concise. No extra commentary.
