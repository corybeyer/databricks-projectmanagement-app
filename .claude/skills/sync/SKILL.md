---
name: sync
description: Pull latest develop into your current feature branch to stay up to date
argument-hint: ""
---

Sync the current feature branch with the latest changes from develop.

Follow these steps exactly:

1. Check for uncommitted changes with `git status --porcelain`.
   - If there are changes, STOP and tell the user to run `/commit` first.

2. Get the current branch name with `git rev-parse --abbrev-ref HEAD`.
   - If on `develop` or `main`, tell the user "You're on $BRANCH. Just run `git pull`." and do that instead.

3. Fetch latest from remote:
   ```
   git fetch origin develop
   ```

4. Merge develop into the current branch:
   ```
   git merge origin/develop
   ```

5. If there are merge conflicts:
   - Show the conflicted files
   - Tell the user which files need manual resolution
   - Do NOT try to auto-resolve conflicts
   - STOP and wait for the user

6. If merge succeeds cleanly, confirm:
   ```
   Synced <branch-name> with latest develop.
   No conflicts.
   ```

Use merge (not rebase) to keep the history straightforward for users who aren't git experts.
