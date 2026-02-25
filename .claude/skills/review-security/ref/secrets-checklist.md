# Secrets & Credentials Checklist

## What Must NEVER Appear in Code

### Databricks-Specific
- [ ] Databricks API tokens (`dapi...` prefix)
- [ ] Actual warehouse IDs (hex strings like `a1b2c3d4e5f67890`)
- [ ] Workspace URLs with embedded tokens
- [ ] Service principal secrets
- [ ] Unity Catalog connection strings

### General Secrets
- [ ] Passwords or password hashes
- [ ] API keys for any service
- [ ] JWT signing secrets
- [ ] SSH private keys
- [ ] TLS/SSL private keys or certificates
- [ ] OAuth client secrets
- [ ] Database connection strings with credentials
- [ ] AWS/Azure/GCP access keys or service account keys

### Grep Patterns to Detect
```bash
# Databricks tokens
grep -rni "dapi[a-f0-9]" --include="*.py" --include="*.yaml" --include="*.yml" --include="*.json"

# Generic secret patterns
grep -rni "password\s*=" --include="*.py" --include="*.yaml"
grep -rni "api_key\s*=" --include="*.py" --include="*.yaml"
grep -rni "secret\s*=" --include="*.py" --include="*.yaml"
grep -rni "token\s*=" --include="*.py" --include="*.yaml"

# Hardcoded strings that look like secrets (long hex/base64)
grep -rn "['\"][a-f0-9]\{32,\}['\"]" --include="*.py"
grep -rn "['\"][A-Za-z0-9+/]\{40,\}=*['\"]" --include="*.py"

# Connection strings
grep -rni "jdbc:" --include="*.py" --include="*.yaml"
grep -rni "postgresql://" --include="*.py" --include="*.yaml"
grep -rni "mysql://" --include="*.py" --include="*.yaml"
```

## .gitignore Requirements

These patterns MUST be in `.gitignore`:

```gitignore
# Environment files
.env
.env.*
.env.local
.env.production

# Keys and certificates
*.pem
*.key
*.p12
*.pfx

# Databricks
.databricks/
.databrickscfg

# IDE secrets
.vscode/settings.json   # May contain tokens
.idea/             # May contain credentials

# Python artifacts
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/

# OS files
.DS_Store
Thumbs.db
```

## Secure Alternatives

| Instead of... | Use... |
|---------------|--------|
| Hardcoded warehouse ID | `os.getenv("DATABRICKS_SQL_WAREHOUSE_ID")` |
| Hardcoded token | OBO auth via `WorkspaceClient()` |
| Secret in app.yaml | Databricks secret scope |
| Password in config | Environment variable + secret manager |
| API key in source | Secret scope: `w.secrets.get_secret(scope, key)` |

## Review Process

1. **Check app.yaml**: No real secrets in `env:` values
2. **Check .gitignore**: All sensitive patterns covered
3. **Grep source code**: Run all patterns above
4. **Check git history**: `git log --diff-filter=A -p -- "*.env" "*.key" "*.pem"`
5. **Check for committed secrets**: Even if removed later, they're in git history
