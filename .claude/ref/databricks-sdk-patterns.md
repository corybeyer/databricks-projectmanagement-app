# Databricks Connection Patterns — Reference Guide

> PM Hub uses **per-user OBO authentication** via `databricks-sql-connector`.
> Every query runs as the logged-in user, respecting Unity Catalog permissions.

## Connection Methods Comparison

| Method | Package | Auth Model | PM Hub? |
|--------|---------|-----------|---------|
| **SQL Connector + OBO token** | `databricks-sql-connector` | User's OAuth token from headers | **YES — approved** |
| SQL Connector + `credentials_provider` | `databricks-sql-connector` | Service principal via `Config()` | NO — service principal auth |
| SDK `statement_execution` | `databricks-sdk` | `WorkspaceClient()` auto-config | NO — service principal auth |
| Databricks Connect | `databricks-connect` | Cluster-level Spark session | NO — wrong use case |

## Approved Pattern: OBO with SQL Connector

### Getting the User Token (Dash/Flask)

```python
from flask import request

def get_user_token() -> str | None:
    """Get the user's OAuth token from Databricks Apps headers."""
    return request.headers.get("X-Forwarded-Access-Token")

def get_user_email() -> str | None:
    """Get the user's email from Databricks Apps headers."""
    return request.headers.get("X-Forwarded-Email")

def get_user_info() -> dict:
    """Get all available user identity from headers."""
    return {
        "email": request.headers.get("X-Forwarded-Email"),
        "username": request.headers.get("X-Forwarded-Preferred-Username"),
        "user": request.headers.get("X-Forwarded-User"),
        "ip": request.headers.get("X-Real-Ip"),
    }
```

**Important**: The `X-Forwarded-Access-Token` header is only available when
OBO (on-behalf-of-user) authentication is enabled on the Databricks App.
Without OBO enabled, you only get basic user identity headers (email, username).

### Creating a Connection (Per-User)

```python
from databricks import sql
from databricks.sdk.core import Config

cfg = Config()  # Reads DATABRICKS_HOST from environment

def get_connection(user_token: str):
    """Create a SQL connection using the user's OAuth token."""
    warehouse_id = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID")
    return sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{warehouse_id}",
        access_token=user_token,
    )
```

### Executing Queries

```python
def execute_query(user_token: str, query: str, params: dict = None) -> pd.DataFrame:
    """Execute a parameterized query as the current user."""
    with get_connection(user_token) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, parameters=params)
            return cursor.fetchall_arrow().to_pandas()
```

### Key Differences from Cookbook Samples

The Databricks Apps Cookbook table recipes use service principal auth:

```python
# COOKBOOK PATTERN — service principal, NOT per-user
conn = sql.connect(
    server_hostname=cfg.host,
    http_path=http_path,
    credentials_provider=lambda: cfg.authenticate,  # <-- service principal
)
```

PM Hub uses explicit user tokens instead:

```python
# PM HUB PATTERN — per-user OBO auth
conn = sql.connect(
    server_hostname=cfg.host,
    http_path=f"/sql/1.0/warehouses/{warehouse_id}",
    access_token=user_token,  # <-- from X-Forwarded-Access-Token header
)
```

**Why**: PM Hub must respect Unity Catalog row/column-level security and
produce audit trails that identify the actual user, not the service principal.

## Anti-Patterns (Flag These)

### 1. Service Principal Auth (credentials_provider)
```python
# FLAG — runs as service principal, not the user
conn = sql.connect(
    server_hostname=cfg.host,
    http_path=http_path,
    credentials_provider=lambda: cfg.authenticate,
)
```
**Why it's wrong**: All queries run as one identity. No per-user UC permissions.

### 2. SDK Statement Execution
```python
# FLAG — WorkspaceClient() authenticates as service principal
w = WorkspaceClient()
result = w.statement_execution.execute_statement(
    warehouse_id=warehouse_id,
    statement=sql,
    catalog="workspace",
    schema="project_management",
)
```
**Why it's wrong**: No per-user auth. Different result handling pattern.

### 3. Hardcoded Tokens
```python
# BLOCK — never hardcode tokens
conn = sql.connect(
    server_hostname="my-workspace.cloud.databricks.com",
    http_path="/sql/1.0/warehouses/abc123",
    access_token="dapi_HARDCODED_TOKEN",
)
```

### 4. Missing Token Validation
```python
# FLAG — must check token exists before using
def get_data():
    token = request.headers.get("X-Forwarded-Access-Token")
    # Missing: what if token is None? (local dev, OBO not enabled)
    return execute_query(token, "SELECT * FROM projects")
```
**Fix**: Always validate the token and fall back to sample data for local dev.

## Result Handling

The SQL Connector returns Arrow tables, converted to pandas:

```python
# Correct — Arrow to pandas
cursor.execute(query, parameters=params)
df = cursor.fetchall_arrow().to_pandas()

# Also acceptable — direct fetch (smaller results)
cursor.execute(query, parameters=params)
rows = cursor.fetchall()
columns = [desc[0] for desc in cursor.description]
df = pd.DataFrame(rows, columns=columns)
```

## Error Handling

```python
from databricks.sql.exc import (
    ServerOperationError,
    RequestError,
    DatabaseError,
)

try:
    df = execute_query(user_token, query, params)
except ServerOperationError as e:
    # Query syntax error, table not found, permission denied
    logger.error(f"SQL error: {e}")
except RequestError as e:
    # Connection timeout, network issues
    logger.error(f"Connection error: {e}")
except DatabaseError as e:
    # General database error
    logger.error(f"Database error: {e}")
```

## Available Headers in Databricks Apps

| Header | Value | Requires OBO? |
|--------|-------|--------------|
| `X-Forwarded-Email` | User's email | No |
| `X-Forwarded-Preferred-Username` | Display name | No |
| `X-Forwarded-User` | User identifier | No |
| `X-Real-Ip` | Client IP | No |
| `X-Forwarded-Access-Token` | OAuth token for OBO queries | **Yes** |

## Local Development

When running locally (`python app.py`), Databricks headers are not available.
The app must detect this and fall back to sample data:

```python
def get_user_token() -> str | None:
    try:
        return request.headers.get("X-Forwarded-Access-Token")
    except RuntimeError:
        # Outside of request context (local dev, testing)
        return None

# In data access layer:
if token is None:
    return sample_data_fallback(query)
```

## Key SDK Imports

```python
# Connection
from databricks import sql
from databricks.sdk.core import Config

# Error handling
from databricks.sql.exc import ServerOperationError, RequestError, DatabaseError
```

## Dependencies

```
databricks-sdk==X.Y.Z
databricks-sql-connector==X.Y.Z
```

Both packages are required: `databricks-sdk` for `Config()` (host resolution),
`databricks-sql-connector` for the actual SQL connection with `access_token`.
