---
name: merge-pr
description: Run lint, tests, and code review, then merge the current PR into develop
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

4. Run code review gate:
   - Run `/review-all` to execute all three review agents (databricks, security, architecture)
   - If the consolidated verdict is **BLOCK** (any CRITICAL findings), STOP and show the findings. Do not merge.
   - If the verdict is **WARN** (HIGH findings only), show findings and ask user to confirm merge anyway
   - If the verdict is **PASS**, continue to next step

5. Show the user the results:
   ```
   Lint: PASSED (or SKIPPED)
   Tests: PASSED (or SKIPPED)
   Review: PASS | WARN | BLOCK
   PR: #<number> — <title>

   Ready to merge?
   ```

6. Once confirmed, merge the PR:
   ```
   gh pr merge <number> --merge --delete-branch
   ```
   Use `--merge` (not squash or rebase) for clear history.

7. Switch back to develop and pull:
   ```
   git checkout develop
   git pull origin develop
   ```

8. Confirm:
   ```
   Merged PR #<number> into develop.
   Branch <branch-name> deleted.
   You're now on develop (up to date).
   ```

IMPORTANT:
- Never merge if lint or tests fail
- Never merge if code review returns BLOCK (CRITICAL findings)
- If code review returns WARN, show findings and get explicit user confirmation
- Never force merge
- Always delete the feature branch after merge
