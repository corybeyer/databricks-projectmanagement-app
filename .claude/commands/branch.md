---
name: branch
description: Create a new git branch following PM Hub naming conventions. Switches to develop, pulls latest, then creates and checks out the new branch.
arguments:
  - name: type
    description: "Branch type: feature, bugfix, schema, hotfix, refactor, or docs"
    required: true
  - name: name
    description: "Short kebab-case description (2-4 words, e.g., risk-register)"
    required: true
---

Create a new git branch following PM Hub conventions.

## Steps

1. Validate the branch type is one of: feature, bugfix, schema, hotfix, refactor, docs
2. Validate the name is kebab-case, lowercase, 2-4 words, no special characters
3. Construct branch name: `{type}/{name}`
4. If type is `hotfix`, branch from `main`. Otherwise branch from `develop`.
5. Run the git commands:
   ```bash
   git checkout {base_branch}
   git pull origin {base_branch}
   git checkout -b {type}/{name}
   ```
6. Confirm the branch was created and tell the user what to do next.

## Validation Rules

- Type must be one of: `feature`, `bugfix`, `schema`, `hotfix`, `refactor`, `docs`
- Name must be lowercase with hyphens only
- Name should be 2-4 words (warn if longer, don't block)
- No underscores, no capitals, no special characters

## Example Usage

```
/branch feature risk-register
/branch schema add-dependencies-table
/branch bugfix velocity-chart-nan
/branch hotfix auth-token-expiry
```
