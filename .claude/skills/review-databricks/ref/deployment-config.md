# Deployment Configuration — Review Rules

## app.yaml

The `app.yaml` file configures the Databricks Apps deployment.

### What MUST NOT appear in app.yaml
- Actual warehouse IDs (use placeholder or environment injection)
- Databricks tokens or API keys
- Database passwords
- Any secret values

### What SHOULD appear in app.yaml
```yaml
command:
  - python
  - app.py

env:
  - name: DATABRICKS_SQL_WAREHOUSE_ID
    value: "your-warehouse-id-here"   # Placeholder — replaced at deploy time
  - name: APP_ENV
    value: "production"
```

### Review Checks
- [ ] No actual warehouse IDs (check for hex patterns like `a1b2c3d4e5f6`)
- [ ] No tokens (check for `dapi` prefix or long hex strings)
- [ ] `APP_ENV` set to appropriate value
- [ ] Command section points to correct entry file

## requirements.txt

### Rules
- **Pin every dependency** with `==` exact versions
- Never use `>=`, `>`, `~=`, or bare package names
- Include transitive dependencies if they have known issues

### Anti-patterns
```
# BAD — unpinned
dash
plotly
pandas

# BAD — range specifier
dash>=2.0
pandas~=2.0

# GOOD — pinned
dash==2.17.1
plotly==5.22.0
pandas==2.2.2
dash-bootstrap-components==1.6.0
databricks-sdk==0.30.0
```

### Review Checks
- [ ] Every package has `==` version pinning
- [ ] `databricks-sdk` is present and pinned
- [ ] No duplicate entries
- [ ] No commented-out packages that should be active

## Environment Variables

### Required in Production
| Variable | Source | Notes |
|----------|--------|-------|
| `DATABRICKS_SQL_WAREHOUSE_ID` | app.yaml / secret scope | SQL warehouse for queries |
| `APP_ENV` | app.yaml | `production` or `development` |

### Must Never Be in Source Code
- `DATABRICKS_TOKEN`
- `DATABRICKS_HOST` (auto-detected in Apps)
- Any database connection strings
- Any API keys for external services

## .gitignore Requirements

The following MUST be in `.gitignore`:
```
.env
.env.*
*.pem
*.key
secrets/
.databricks/
__pycache__/
*.pyc
.pytest_cache/
```
