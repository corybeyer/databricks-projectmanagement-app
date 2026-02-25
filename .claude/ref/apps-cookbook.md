# Databricks Apps Cookbook — Reference Summary

> Pre-fetched from [apps-cookbook.dev](https://apps-cookbook.dev) on 2026-02-25.
> Source: [GitHub — databricks-solutions/databricks-apps-cookbook](https://github.com/databricks-solutions/databricks-apps-cookbook)

## Overview

The Databricks Apps Cookbook provides ready-to-use code snippets for building interactive data and AI applications using Databricks Apps. Supports Dash, Streamlit, FastAPI, and Reflex.

**Important**: These samples are experimental and meant for demonstration purposes. Apply your organization's security and compliance standards before production use.

## Dash Recipes Available

| Category | Recipes | Key Topics |
|----------|---------|------------|
| Tables | 3 | Data table read/write, OLTP database |
| Volumes | 2 | File storage, upload to Unity Catalog Volumes |
| AI/ML | 3 | Model serving invocation, MCP server connection |
| Workflows | 2 | Trigger Databricks jobs |
| AI/BI | 2 | Embed dashboards |
| Compute | 1 | Cluster connection via Databricks Connect |
| Authentication | 1 | Get current user identity |
| External Services | 2 | Third-party integrations |

## Authentication — Get Current User

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
- `X-Forwarded-Access-Token` — OBO token (requires OBO auth enabled)

**Note**: Without OBO authentication enabled, `WorkspaceClient().current_user.me()` returns the **app service principal** info, not the actual user.

## OLTP Database Connection (Lakebase)

For apps needing OLTP (read/write) database access via Lakebase PostgreSQL:

### Pattern: Rotating Token Connection Pool
```python
# Uses WorkspaceClient.database.generate_database_credential()
# for fresh OAuth tokens with connection pooling

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

### Query Pattern
```python
def query_df(sql: str) -> pd.DataFrame:
    """Execute SQL and return pandas DataFrame via connection pool."""
    with pool.connection() as conn:
        return pd.read_sql(sql, conn)
```

## Compute — Connect to a Cluster

Use Databricks Connect for Spark SQL on shared clusters:

```python
from databricks.connect import DatabricksSession
import os

cluster_id = "your-cluster-id"
spark = DatabricksSession.builder.remote(
    host=os.getenv("DATABRICKS_HOST"),
    cluster_id=cluster_id
).getOrCreate()

# Execute SQL and convert to pandas
df = spark.sql("SELECT * FROM my_table").toPandas()
```

**Permissions**: Service principal needs `CAN ATTACH TO` on the cluster.
**Alternative**: Use serverless compute for simplified infrastructure.

## Deployment

### Via Workspace UI
1. Compute → Apps → Create App → Custom
2. Name your app → Create App
3. Once compute starts → Deploy → Select folder from Git repo

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

1. **Auth**: Is OBO enabled if user identity is needed? Are headers used correctly?
2. **SDK**: Is `WorkspaceClient()` initialized without hardcoded credentials?
3. **SQL**: Are queries parameterized? Is the connection pattern safe?
4. **Deploy**: Does `app.yaml` follow the cookbook structure? No secrets in config?
5. **Dependencies**: Are versions pinned in `requirements.txt`?
6. **Compute**: If using Databricks Connect, are permissions configured correctly?
