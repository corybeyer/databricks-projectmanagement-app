---
name: git-standards
description: Git workflow standards for PM Hub. Auto-loads when Claude detects git operations — branching, committing, merging, or PR creation. Provides branching strategy, commit conventions, PR templates, and merge rules.
triggers:
  - git
  - branch
  - commit
  - merge
  - pull request
  - PR
  - push
---

# PM Hub Git Standards

## Branch Strategy

```
main              ← Production. Auto-deploys to Databricks Apps.
└── develop       ← Integration. All feature work merges here first.
    ├── feature/* ← New features: feature/risk-register
    ├── bugfix/*  ← Fixes: bugfix/velocity-chart-nan
    ├── schema/*  ← DDL changes: schema/add-dependencies-table
    └── hotfix/*  ← Urgent: hotfix/auth-token-expiry (from main)
```

### Branch Naming Rules

Format: `{type}/{short-kebab-case-description}`

- **2-4 words** max in the description
- **Lowercase** only, hyphens between words
- **No ticket numbers** unless the team adopts a ticketing system later
- Type must be one of: `feature`, `bugfix`, `schema`, `hotfix`, `docs`, `refactor`

Valid examples:
- `feature/portfolio-dashboard`
- `feature/risk-heatmap`
- `bugfix/kanban-status-update`
- `schema/add-gates-table`
- `hotfix/warehouse-connection`
- `docs/update-readme`
- `refactor/extract-chart-components`

Invalid examples:
- `new-feature` (missing type prefix)
- `feature/Add_Risk_Register` (uppercase, underscores)
- `feature/this-is-a-really-long-branch-name-that-goes-on-forever` (too long)

### Branching Rules

1. **feature/**, **bugfix/**, **schema/**, **refactor/** → branch from `develop`, PR into `develop`
2. **hotfix/** → branch from `main`, PR into BOTH `main` and `develop`
3. **Never** push directly to `main` or `develop`
4. **Delete** branches after merge

### Merge Rules

- `develop` → `main`: Only when a set of features is tested and ready for deployment
- Squash merges encouraged for feature branches (cleaner history)
- Merge commits for `develop` → `main` (preserve the release boundary)

## Commit Message Convention

### Format

```
type: short description in imperative mood
```

- **Imperative mood**: "add feature" not "added feature" or "adding feature"
- **Lowercase**: No capital letters in the description
- **No period** at the end
- **50 characters max** for the short description

### Types

| Type | When to Use | Example |
|------|-------------|---------|
| `feat` | New feature, page, or capability | `feat: add sprint board kanban view` |
| `fix` | Bug fix | `fix: correct burndown remaining points calc` |
| `refactor` | Code change, no behavior change | `refactor: extract task card component` |
| `schema` | DDL, migrations, table changes | `schema: add risk_score computed column` |
| `style` | CSS, UI-only, formatting | `style: update kanban card hover states` |
| `docs` | Documentation changes | `docs: update CLAUDE.md with phase 3 state` |
| `test` | Test files | `test: add portfolio query validation` |
| `deploy` | CI/CD, app.yaml, GitHub Actions | `deploy: add staging environment workflow` |
| `chore` | Dependencies, cleanup | `chore: pin plotly to 5.24.1` |

### Multi-line Commits (for larger changes)

```
feat: add risk management page

- Risk register table with P×I scoring
- 5×5 probability-impact heatmap
- Response plan cards with trigger tracking
- Timeline audit trail via Delta time travel
- PMI 6-step process reference tab
```

Body lines start with `- ` and describe what was done.

## Pull Request Standards

### PR Title

Same format as commit messages: `type: short description`

### PR Body Template

```markdown
## What

Brief description of what this PR does.

## Why

Business or technical reason for the change.

## Schema Changes

- [ ] No schema changes
- [ ] Migration script added to models/migrations/
- [ ] schema_ddl.sql updated

## Testing

- [ ] Tested locally with `python app.py`
- [ ] Sample data fallback works
- [ ] No broken imports

## Screenshots

(If UI changes, paste before/after screenshots)
```

### PR Rules

1. Every PR needs at least a self-review before merge
2. Schema changes require extra scrutiny — flag with `schema/` branch prefix
3. Keep PRs focused — one feature or fix per PR
4. Update CLAUDE.md if architecture decisions change

## Release Process

When `develop` is ready for production:

1. Create PR: `develop` → `main`
2. Title: `release: v0.X.0 — brief description`
3. Body: List all features/fixes since last release
4. Merge (not squash — preserve history)
5. GitHub Actions auto-deploys to Databricks Apps
6. Verify deployment: `databricks apps get pm-hub`
