# Databricks Apps Cookbook — Reference Summary

> Pre-fetched from [apps-cookbook.dev](https://apps-cookbook.dev) on 2026-02-25.
> Source: [GitHub — databricks-solutions/databricks-apps-cookbook](https://github.com/databricks-solutions/databricks-apps-cookbook)

## Overview

The Databricks Apps Cookbook provides ready-to-use code snippets for building interactive data and AI applications using Databricks Apps. Supports Dash, Streamlit, FastAPI, and Reflex.

**Important**: The cookbook samples use **service principal auth** by default.
PM Hub requires **per-user OBO auth** instead. See `databricks-sdk-patterns.md`
for the approved connection pattern. When reviewing code, do NOT treat cookbook
samples as the correct auth pattern — they must be adapted for OBO.

## Dash Recipes Available

| Category | Recipes | Auth Model | PM Hub Applicable? |
|----------|---------|-----------|-------------------|
| Tables — Read | 1 | Service principal (`credentials_provider`) | Pattern only — must swap to OBO |
| Tables — Edit | 1 | Service principal (`credentials_provider`) | Parameterization pattern is useful |
| Tables — OLTP (Lakebase) | 1 | Service principal (`WorkspaceClient`) | Not used — PM Hub uses UC directly |
| Authentication | 1 | Headers (Flask `request.headers`) | **Yes — directly applicable** |
| Volumes | 2 | Service principal | Not yet needed |
| AI/ML | 3 | Service principal | Not yet needed |
| Workflows | 2 | Service principal | Not yet needed |
| AI/BI | 2 | Service principal | Not yet needed |
| Compute | 1 | Service principal | Not used |
| External Services | 2 | Service principal | Not yet needed |

## Authentication — Get Current User (Directly Applicable)

Access user info from HTTP headers (Flask/Dash):

```python
from flask import request

headers = request.headers
email = headers.get("X-Forwarded-Email")
username = headers.get("X-Forwarded-Preferred-Username")
user = headers.get("X-Forwarded-User")
ip = headers.get("X-Real-Ip")
```

**Key headers available in Databricks Apps:**
- `X-Forwarded-Email` — User's email
- `X-Forwarded-Preferred-Username` — Display name
- `X-Forwarded-User` — User identifier
- `X-Real-Ip` — Client IP
- `X-Forwarded-Access-Token` — OBO token (**requires OBO auth enabled**)

**Critical note**: Without OBO authentication enabled:
- You still get user identity headers (email, username)
- You do NOT get `X-Forwarded-Access-Token`
- `WorkspaceClient().current_user.me()` returns the **app service principal**, not the user
- SQL queries run as the service principal, not the user

**PM Hub requires OBO enabled** to get the access token for per-user SQL queries.

## Cookbook Table Patterns (Service Principal — NOT for PM Hub Auth)

### Read a Delta Table (Cookbook Pattern)
```python
# WARNING: This uses service principal auth (credentials_provider)
# PM Hub must use access_token=user_token instead
from functools import lru_cache
from databricks import sql
from databricks.sdk.core import Config

cfg = Config()

@lru_cache(maxsize=1)
def get_connection(http_path):
    return sql.connect(
        server_hostname=cfg.host,
        http_path=http_path,
        credentials_provider=lambda: cfg.authenticate,  # <-- service principal
    )

def read_table(table_name, conn):
    with conn.cursor() as cursor:
        query = f"SELECT * FROM {table_name}"  # <-- also not parameterized
        cursor.execute(query)
        return cursor.fetchall_arrow().to_pandas()
```

**What to take from this**: The `sql.connect()` + `cursor.fetchall_arrow().to_pandas()`
pattern is correct. The auth method and lack of parameterization are not.

### Edit a Delta Table (Cookbook Pattern)
```python
# WARNING: Same service principal auth issue
# But the parameterized write pattern IS useful

def insert_overwrite_table(table_name: str, df: pd.DataFrame, conn):
    with conn.cursor() as cursor:
        rows = list(df.itertuples(index=False, name=None))
        if not rows:
            return
        cols = list(df.columns)
        params = {}
        values_sql_parts = []
        p = 0
        for row in rows:
            ph = []
            for v in row:
                key = f"p{p}"
                ph.append(f":{key}")
                params[key] = v
                p += 1
            values_sql_parts.append("(" + ",".join(ph) + ")")
        values_sql = ",".join(values_sql_parts)
        col_list_sql = ",".join(cols)
        cursor.execute(
            f"INSERT OVERWRITE {table_name} ({col_list_sql}) VALUES {values_sql}",
            params
        )
```

**What to take from this**: The parameterized `:param_name` syntax with a
dict passed to `cursor.execute()` is the correct parameterization approach
for `databricks-sql-connector`.

## OLTP Database — Lakebase (Not Used by PM Hub)

The cookbook shows Lakebase (Databricks-managed PostgreSQL) for OLTP workloads.
PM Hub's architecture plan originally considered standalone Postgres but this
is a future decision. Documenting for reference only.

### Pattern: Rotating Token Connection Pool
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
token = w.database.generate_database_credential(
    request_id=str(uuid.uuid4())
)
# Token used as password for PostgreSQL connection with sslmode=require
```

### Requirements
- `databricks-sdk >= 0.60.0`
- `psycopg[binary]`, `psycopg-pool`
- Service principal needs: CONNECT, USAGE, CREATE, SELECT grants
- Lakebase PostgreSQL instance in app resources

## Deployment

### Via Workspace UI
1. Compute > Apps > Create App > Custom
2. Name your app > Create App
3. Once compute starts > Deploy > Select folder from Git repo

### Via Local Development
```bash
git clone <repo>
cd databricks-apps-cookbook/dash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
python app.py
```

### app.yaml Structure
```yaml
command:
  - python
  - app.py

env:
  - name: DATABRICKS_SQL_WAREHOUSE_ID
    value: "your-warehouse-id"
  - name: APP_ENV
    value: "production"
```

### CI/CD with GitHub Actions + DABs
Databricks Asset Bundles (DABs) support automated deployments via:
- Databricks REST API
- Databricks CLI
- Python SDK
- Terraform

## Review Agent Checks Based on Cookbook

When reviewing PM Hub against cookbook patterns:

1. **Auth**: OBO must be enabled. User token from `X-Forwarded-Access-Token` header must be used for all SQL connections. `credentials_provider` is NOT acceptable.
2. **Connection**: `sql.connect()` with `access_token=user_token` — never `credentials_provider=lambda: cfg.authenticate`
3. **SQL**: All queries parameterized with `:param_name` + dict. No f-strings with user data.
4. **Results**: `cursor.fetchall_arrow().to_pandas()` for reads.
5. **Deploy**: `app.yaml` follows cookbook structure. No secrets in config.
6. **Dependencies**: Versions pinned in `requirements.txt`.
7. **Local dev**: Token fallback to sample data when headers unavailable.
