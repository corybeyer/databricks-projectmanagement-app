---
name: pr
description: Push current branch and create a pull request into develop
argument-hint: "[optional PR title]"
---

Push the current branch and open a pull request into develop.

Follow these steps exactly:

1. Check for uncommitted changes with `git status --porcelain`.
   - If there are changes, STOP and tell the user to run `/commit` first.

2. Get the current branch with `git rev-parse --abbrev-ref HEAD`.
   - If on `develop` or `main`, STOP and tell the user "You can't open a PR from $BRANCH. Use /start-feature first."

3. Push the branch to remote:
   ```
   git push -u origin <branch-name>
   ```

4. Gather PR context:
   - Run `git log develop..HEAD --oneline` to see all commits in this branch
   - Run `git diff develop...HEAD --stat` to see files changed

5. Draft a PR title and body:
   - If $ARGUMENTS is provided, use it as the title
   - Otherwise, derive a title from the branch name and commits
   - Keep title under 70 characters

6. Create the PR:
   ```
   gh pr create --base develop --title "<title>" --body "$(cat <<'EOF'
   ## Summary
   <2-3 bullet points summarizing the changes>

   ## Changes
   <list of key files/areas changed>

   ## Test plan
   - [ ] App starts without errors (`python app.py`)
   - [ ] Affected pages load correctly
   - [ ] No import errors

   Generated with [Claude Code](https://claude.com/claude-code)
   EOF
   )"
   ```

7. Show the user the PR URL when done.

IMPORTANT:
- Always target `develop` as the base branch (unless this is a hotfix targeting main)
- Never force push
