---
name: hotfix
description: Create an emergency hotfix branch from main (merges to both main and develop)
argument-hint: [branch-name]
---

Create a hotfix branch for an emergency fix. Hotfixes branch from main and merge to BOTH main and develop.

Follow these steps exactly:

1. Check for uncommitted changes with `git status --porcelain`.
   - If there are changes, STOP and tell the user to commit or stash first.

2. Pull latest main:
   ```
   git checkout main
   git pull origin main
   ```

3. Create the hotfix branch:
   ```
   git checkout -b hotfix/$ARGUMENTS
   ```

4. Confirm:
   ```
   Created branch: hotfix/$ARGUMENTS
   Based on: main (up to date)

   HOTFIX WORKFLOW:
   1. Make your fix
   2. /commit to save
   3. /pr to open PR into main (not develop)
   4. After merging to main, also merge into develop
   ```

If no argument is provided, ask the user to name the hotfix.

IMPORTANT:
- Hotfixes target MAIN, not develop
- After merging to main, the user must also merge the changes into develop
- Remind the user of this at every step
