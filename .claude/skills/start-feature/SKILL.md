---
name: start-feature
description: Create a new feature branch from develop following the project branch strategy
argument-hint: [branch-name]
---

Create a new feature branch for the user. The argument $ARGUMENTS is the branch name (without the prefix).

Follow these steps exactly:

1. Check for uncommitted changes with `git status --porcelain`. If there are any, STOP and tell the user to commit or stash first. Do not proceed.

2. Switch to develop and pull latest:
   ```
   git checkout develop
   git pull origin develop
   ```

3. Determine the branch prefix from the name:
   - If $ARGUMENTS starts with "bugfix/" or "hotfix/" or "feature/", use it as-is
   - Otherwise, default to `feature/$ARGUMENTS`

4. Create and switch to the new branch:
   ```
   git checkout -b <branch-name>
   ```

5. Confirm to the user:
   ```
   Created branch: <branch-name>
   Based on: develop (up to date)
   Ready to work.
   ```

If no argument is provided, ask the user what they want to call the branch. Suggest a name based on recent conversation context if possible.

Branch naming rules (from CLAUDE.md):
- Format: `{type}/{short-kebab-description}`
- Examples: `feature/layered-architecture`, `bugfix/chart-colors`, `feature/sprint-page`
- Lowercase, hyphens, no spaces
