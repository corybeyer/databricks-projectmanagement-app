---
name: pr
description: Create a pull request with the PM Hub template. Analyzes the branch diff, generates title and body, and opens the PR using GitHub CLI.
arguments:
  - name: title
    description: "Optional: PR title override. If omitted, generated from branch name and commits."
    required: false
---

Create a pull request following PM Hub standards.

## Steps

1. Get the current branch name: `git branch --show-current`
2. Determine the target branch:
   - If current branch starts with `hotfix/` → target is `main`
   - Otherwise → target is `develop`
3. Get the commit log for this branch: `git log develop..HEAD --oneline` (or main for hotfixes)
4. Analyze the commits and changed files to generate:
   - **PR title**: Same convention as commits (`type: short description`)
   - **What section**: Brief summary of the changes
   - **Why section**: Infer from the feature/fix context
   - **Schema changes**: Check if any `.sql` or `models/` files changed
   - **Testing checklist**: Pre-filled based on what changed
5. If the user provided a title, use it (validate format).
6. Generate the PR body using the template.
7. Push the branch and create the PR:
   ```bash
   git push origin {current_branch}
   gh pr create --base {target} --title "{title}" --body "{body}"
   ```
8. If `gh` CLI is not available, output the PR body as markdown and give 
   instructions to create it manually on github.com.

## PR Body Template

```markdown
## What

{Generated summary of changes}

## Why

{Inferred business/technical reason}

## Changes

{List of key file changes with brief descriptions}

## Schema Changes

- [x/] No schema changes
- [x/] Migration script in models/migrations/
- [x/] schema_ddl.sql updated

## Testing

- [ ] Tested locally with `python app.py`
- [ ] Sample data fallback works
- [ ] No broken imports
- [ ] Charts render correctly

## Screenshots

{Note: add screenshots if UI changes}
```

## Example

Branch: `feature/risk-register`

Generated PR:
```
Title: feat: add risk management page with PMI framework

## What
Adds the risk register page with full PMI 6-step risk management support.

## Why
Enables systematic risk tracking following PMI standards. Replaces ad hoc
spreadsheet-based risk management.

## Changes
- `pages/risks.py` — New page with register table, heatmap, response cards
- `utils/data_access.py` — Added get_risks(), get_risk_detail() queries
- `utils/charts.py` — Added risk_heatmap() chart builder
- `app.py` — Added nav link for /risks route

## Schema Changes
- [ ] No schema changes

## Testing
- [ ] Tested locally with `python app.py`
- [ ] Sample data fallback works
- [ ] Heatmap renders with sample risk data
```
