---
name: merge-pr
description: Run lint and tests, then merge the current PR into develop
argument-hint: "[optional PR number]"
---

Run quality checks and merge the pull request for the current branch (or a specific PR number).

Follow these steps exactly:

1. Determine the PR:
   - If $ARGUMENTS is a number, use that as the PR number
   - Otherwise, find the PR for the current branch: `gh pr view --json number,title,state`
   - If no PR exists, STOP and tell the user to run `/pr` first

2. Run lint:
   ```
   ruff check .
   ```
   - If ruff is not installed, skip lint and note it was skipped
   - If lint fails, show the errors and STOP. Do not merge.

3. Run tests:
   ```
   pytest tests/ -v
   ```
   - If pytest is not installed or no tests exist, skip and note it was skipped
   - If tests fail, show the failures and STOP. Do not merge.

4. Show the user the results:
   ```
   Lint: PASSED (or SKIPPED)
   Tests: PASSED (or SKIPPED)
   PR: #<number> — <title>

   Ready to merge?
   ```

5. Once confirmed, merge the PR:
   ```
   gh pr merge <number> --merge --delete-branch
   ```
   Use `--merge` (not squash or rebase) for clear history.

6. Switch back to develop and pull:
   ```
   git checkout develop
   git pull origin develop
   ```

7. Confirm:
   ```
   Merged PR #<number> into develop.
   Branch <branch-name> deleted.
   You're now on develop (up to date).
   ```

IMPORTANT:
- Never merge if lint or tests fail
- Never force merge
- Always delete the feature branch after merge
