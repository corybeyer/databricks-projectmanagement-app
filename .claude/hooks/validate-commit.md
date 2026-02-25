---
name: validate-commit
description: Pre-commit validation hook. Runs automatically before every commit to check message format, branch naming, and code quality basics.
trigger: pre-commit
---

# Pre-Commit Validation

Run these checks before every commit. If any fail, warn the user and suggest fixes.

## Checks

### 1. Commit Message Format

Validate the commit message matches: `type: lowercase description`

Valid types: `feat`, `fix`, `refactor`, `schema`, `style`, `docs`, `test`, `deploy`, `chore`

Rules:
- Must start with a valid type
- Followed by `: ` (colon then space)
- Description in lowercase
- No period at the end
- First line under 50 characters

If invalid, suggest the corrected format.

### 2. Branch Name

Check the current branch name follows convention:
- Must match pattern: `{type}/{kebab-case-name}`
- Type is one of: `feature`, `bugfix`, `schema`, `hotfix`, `refactor`, `docs`
- Or is `main` or `develop` (acceptable but warn if committing directly)

If on `main` or `develop`, warn: "You're committing directly to {branch}. Consider using a feature branch."

### 3. No Secrets

Scan staged files for potential secrets:
- Strings matching `dapi*` (Databricks tokens)
- Strings matching `sk-*` (API keys)
- Files named `.env`, `.env.local`
- Any file containing `DATABRICKS_TOKEN` with an actual value

If found, block the commit and warn.

### 4. No SQL in Pages

Check if any file in `pages/` contains raw SQL strings (SELECT, INSERT, UPDATE, CREATE).
If found, warn: "SQL found in page file. Move queries to utils/data_access.py"

### 5. Schema DDL Consistency

If any `.sql` file in `models/` was modified:
- Check that a migration file exists in `models/migrations/`
- Warn if `schema_ddl.sql` was modified without a corresponding migration
