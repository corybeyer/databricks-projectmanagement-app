# Databricks SDK Patterns — Reference Guide

## WorkspaceClient Initialization

### Correct Pattern (OBO Auth in Databricks Apps)
```python
from databricks.sdk import WorkspaceClient

# Inside a Databricks App, WorkspaceClient() auto-detects credentials
# via On-Behalf-Of (OBO) authentication — no tokens needed
w = WorkspaceClient()
```

### Anti-patterns
```python
# NEVER hardcode tokens
w = WorkspaceClient(token="dapi123...")  # BAD

# NEVER read tokens from config files
w = WorkspaceClient(token=config["token"])  # BAD

# NEVER disable SSL verification
w = WorkspaceClient(verify=False)  # BAD
```

## Statement Execution

### Correct Pattern (Parameterized)
```python
result = w.statement_execution.execute_statement(
    warehouse_id=os.getenv("DATABRICKS_SQL_WAREHOUSE_ID"),
    statement="SELECT * FROM projects WHERE portfolio_id = :portfolio_id",
    catalog="workspace",
    schema="project_management",
    parameters=[
        StatementParameterListItem(name="portfolio_id", value=portfolio_id, type="STRING")
    ]
)
```

### Anti-pattern (F-string Interpolation)
```python
# VULNERABLE — SQL injection risk
result = w.statement_execution.execute_statement(
    warehouse_id=os.getenv("DATABRICKS_SQL_WAREHOUSE_ID"),
    statement=f"SELECT * FROM projects WHERE portfolio_id = '{portfolio_id}'",
    catalog="workspace",
    schema="project_management",
)
```

## Result Handling

### Converting to DataFrame
```python
from databricks.sdk.service.sql import StatementState

# Check execution status
if result.status.state != StatementState.SUCCEEDED:
    raise RuntimeError(f"Query failed: {result.status.error}")

# Extract columns and rows
columns = [col.name for col in result.manifest.schema.columns]
rows = []
if result.result and result.result.data_array:
    rows = result.result.data_array

df = pd.DataFrame(rows, columns=columns)
```

### Handling Large Results (Chunked)
```python
# For large result sets, use external links
result = w.statement_execution.execute_statement(
    warehouse_id=warehouse_id,
    statement=sql,
    disposition="EXTERNAL_LINKS",  # For large results
    catalog="workspace",
    schema="project_management",
)
```

## Error Handling

```python
from databricks.sdk.errors import NotFound, PermissionDenied, ResourceConflict

try:
    result = w.statement_execution.execute_statement(...)
except NotFound:
    # Warehouse not found or table doesn't exist
    logger.error("Resource not found")
except PermissionDenied:
    # User lacks access to the table/warehouse
    logger.error("Permission denied")
except Exception as e:
    # Connection timeout, network issues
    logger.error(f"SDK error: {e}")
```

## Key SDK Imports

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import (
    ExecuteStatementRequest,
    StatementParameterListItem,
    StatementState,
)
```

## Databricks Apps Specifics

- **OBO Auth**: `WorkspaceClient()` with no args uses the app's service principal + user's identity
- **Environment variables**: Use `app.yaml` `env:` section for config, accessed via `os.getenv()`
- **Warehouse ID**: Always from environment variable, never hardcoded
- **Secrets**: Use Databricks secret scopes, not `app.yaml` values
