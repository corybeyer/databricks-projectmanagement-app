---
description: Stage changes, write a conventional commit message, and commit
allowed-tools: Bash(git *)
---

Help the user commit their current changes. Follow these steps exactly:

1. Run `git status` to see what's changed (staged and unstaged).
   - If there are no changes at all, tell the user "Nothing to commit" and stop.

2. Run `git diff` (unstaged) and `git diff --staged` (staged) to understand what changed.

3. Draft a conventional commit message following the project standard:
   ```
   type: short description (imperative mood, lowercase)
   ```
   Valid types: feat, fix, refactor, schema, style, docs, test, deploy, chore

   If the user provided $ARGUMENTS, use that as the commit message instead (but validate it follows the format).

4. Show the user:
   - Files that will be committed
   - The proposed commit message
   - Ask for confirmation before proceeding

5. Once confirmed, stage the relevant files:
   - Use `git add <specific files>` — prefer specific files over `git add -A`
   - Never stage `.env` files or anything in `.gitignore`

6. Commit using a heredoc for proper formatting:
   ```
   git commit -m "$(cat <<'EOF'
   type: description

   Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
   EOF
   )"
   ```

7. After commit succeeds, ask: "Push to remote?" If yes, run `git push -u origin <branch-name>`.

IMPORTANT:
- Always include the Co-Authored-By trailer
- Never amend previous commits unless the user explicitly asks
- If a pre-commit hook fails, fix the issue and create a NEW commit
- Never use --no-verify
