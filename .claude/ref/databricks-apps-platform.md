# Databricks Apps Platform Rules — Reference Guide

> Source: [Microsoft Learn — Databricks Apps](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/)
> Fetched: 2026-02-25

Rules and constraints the review agent must validate. Covers app structure,
runtime environment, resource configuration, and best practices.

## Runtime Environment

| Property | Value |
|----------|-------|
| OS | Ubuntu 22.04 LTS |
| Python | 3.11 (isolated venv per app) |
| Default compute | 2 vCPUs, 6 GB memory |
| File size limit | **10 MB per file** — deployment fails if exceeded |
| Shutdown signal | `SIGTERM` — app must exit within **15 seconds** or gets `SIGKILL` |
| Bind address | Must listen on `0.0.0.0` at port `DATABRICKS_APP_PORT` |

## Pre-installed Python Libraries (No need to pin in requirements.txt)

| Library | Pre-installed Version |
|---------|----------------------|
| `databricks-sql-connector` | 3.4.0 |
| `databricks-sdk` | 0.33.0 |
| `dash` | 2.18.1 |
| `flask` | 3.0.3 |
| `dash-bootstrap-components` | 1.6.0 |
| `dash-ag-grid` | 31.2.0 |
| `dash-mantine-components` | 0.14.4 |
| `plotly` | 5.24.1 |
| `plotly-resampler` | 0.10.0 |
| `gunicorn` | 23.0.0 |
| `mlflow-skinny` | 2.16.2 |
| `gradio` | 4.44.0 |
| `streamlit` | 1.38.0 |
| `fastapi` | 0.115.0 |
| `uvicorn[standard]` | 0.30.6 |
| `huggingface-hub` | 0.35.3 |

**Override rule**: If `requirements.txt` includes a pre-installed package,
the specified version overrides the default. Pin versions explicitly to
avoid surprises from platform updates.

## Default Environment Variables

Available in every app without configuration:

| Variable | Description |
|----------|-------------|
| `DATABRICKS_APP_NAME` | Name of the running app |
| `DATABRICKS_WORKSPACE_ID` | Workspace unique ID |
| `DATABRICKS_HOST` | Workspace URL |
| `DATABRICKS_APP_PORT` | Port the app must listen on |
| `DATABRICKS_CLIENT_ID` | Service principal OAuth client ID |
| `DATABRICKS_CLIENT_SECRET` | Service principal OAuth client secret |

**Review check**: Code should use `os.getenv("DATABRICKS_HOST")` or
`Config().host` — never hardcode workspace URLs.

## App URL Format

```
https://<app-name>-<workspace-id>.<region>.databricksapps.com
```

URL is assigned at creation and cannot be changed.

## app.yaml Configuration

### Structure
```yaml
command:
  - python
  - app.py

env:
  - name: WAREHOUSE_ID
    valueFrom: sql_warehouse    # References a configured resource
  - name: APP_ENV
    value: "production"         # Static, non-sensitive values only
```

### Rules
- `command` is optional — defaults to `python <first .py file>`
- Commands do NOT run in a shell — env vars defined outside app.yaml are unavailable
- Use `valueFrom` for secrets and resource references, never `value` with sensitive data
- Use `value` only for static, non-sensitive configuration

### Review Checks for app.yaml
- [ ] No actual warehouse IDs, tokens, or passwords in `value` fields
- [ ] Secrets use `valueFrom` referencing a secret resource
- [ ] SQL warehouse uses `valueFrom` referencing a sql-warehouse resource
- [ ] Command points to correct entry file
- [ ] No Streamlit-specific settings (this is a Dash app)

## App Resources

Resources are declared in the Databricks Apps UI during deployment, not in code.
The app references them via environment variables set by `valueFrom` in app.yaml.

### Supported Resource Types

| Resource | Key | PM Hub Relevant? |
|----------|-----|-----------------|
| SQL warehouse | `sql-warehouse` | **Yes** — primary query compute |
| Secret | `secret` | **Yes** — sensitive config values |
| Unity Catalog volume | `volume` | Maybe — file storage |
| Lakebase database | `database` | Future consideration |
| Lakeflow job | `job` | Future — ETL workflows |
| Model serving endpoint | `serving-endpoint` | Future — AI features |
| Genie space | `genie-space` | Not planned |
| MLflow experiments | `experiment` | Not planned |
| Vector search index | `vector-search-index` | Not planned |
| UC connection | `connection` | Not planned |
| UC function | `function` | Not planned |

### Resource Permissions (Least Privilege)
- SQL warehouse: `CAN USE` (not `CAN MANAGE`)
- Secrets: `CAN READ` (not `CAN MANAGE`)
- UC tables: `SELECT` for reads, `MODIFY` for writes

## App State

**In-memory state is lost on restart.** Apps must not depend on in-memory
persistence across sessions or deployments.

Persistent state options:
- **Unity Catalog tables** — structured data, analytics (PM Hub primary)
- **Unity Catalog volumes** — unstructured files with governance
- **Lakebase** — PostgreSQL-compatible OLTP (future consideration)
- **Workspace files** — unstructured files without UC governance

**Review check**: No app logic should assume in-memory state survives restarts.
Session data, caches, and user preferences must be stored externally or
be rebuildable.

## Best Practices (from Microsoft — Enforce These)

### Performance
- [ ] Offload data processing to SQL warehouses — app compute is for UI rendering
- [ ] Use in-memory caching (`lru_cache`, `cachetools`) for expensive operations
- [ ] Use async patterns for long-running operations — don't block on synchronous waits
- [ ] Minimize container startup time — no heavy operations during init

### Security
- [ ] Parameterize SQL queries — prevent injection attacks
- [ ] Validate and sanitize all user input
- [ ] Never expose stack traces or sensitive data in error responses
- [ ] Pin dependency versions in requirements.txt
- [ ] Use `valueFrom` for secrets — never hardcode in app.yaml or source code
- [ ] Follow principle of least privilege for all resource permissions

### Operations
- [ ] Log to stdout/stderr only — Databricks captures these automatically
- [ ] Implement graceful `SIGTERM` handling (15-second window)
- [ ] Bind to `0.0.0.0` on `DATABRICKS_APP_PORT`
- [ ] Handle unexpected errors with global exception handling
- [ ] Don't implement custom TLS — Databricks handles TLS termination
- [ ] App must support HTTP/2 cleartext (H2C)

### Networking
- [ ] Don't depend on request origin — reverse proxy forwards all requests
- [ ] No custom TLS handling — Databricks terminates TLS

## Dash-Specific Notes

Dash runs on Flask, so:
- User headers accessed via `flask.request.headers`
- App binds via `app.run(host="0.0.0.0", port=os.getenv("DATABRICKS_APP_PORT"))`
- Pre-installed: `dash==2.18.1`, `dash-bootstrap-components==1.6.0`, `plotly==5.24.1`
- `gunicorn` is pre-installed for production WSGI serving

### Dash app.yaml Example
```yaml
command:
  - python
  - app.py

env:
  - name: WAREHOUSE_ID
    valueFrom: sql_warehouse
```

Or with gunicorn for production:
```yaml
command:
  - gunicorn
  - app:server
  - -w
  - "4"
  - -b
  - "0.0.0.0:${DATABRICKS_APP_PORT}"

env:
  - name: WAREHOUSE_ID
    valueFrom: sql_warehouse
```
