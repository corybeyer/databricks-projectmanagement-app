# Parameterized Queries — Migration Guide

> PM Hub uses `databricks-sql-connector` with per-user OBO auth.
> Parameterization uses the connector's native `parameters=` argument.

## The Problem

PM Hub currently uses f-string interpolation for SQL queries in `utils/data_access.py`. While these run inside Unity Catalog's auth context, they are still vulnerable to SQL injection if any user-controlled input reaches the query functions.

### Current Pattern (Vulnerable)
```python
def get_portfolio_projects(portfolio_id: str) -> pd.DataFrame:
    return query(f"""
        SELECT pr.*, ph.name as current_phase_name
        FROM projects pr
        LEFT JOIN phases ph ON pr.current_phase_id = ph.phase_id
        WHERE pr.portfolio_id = '{portfolio_id}'
        AND pr.is_active = true
        ORDER BY pr.project_name
    """)
```

### Target Pattern (Safe)
```python
def get_portfolio_projects(portfolio_id: str, user_token: str) -> pd.DataFrame:
    return query(
        """
        SELECT pr.*, ph.name as current_phase_name
        FROM projects pr
        LEFT JOIN phases ph ON pr.current_phase_id = ph.phase_id
        WHERE pr.portfolio_id = :portfolio_id
        AND pr.is_active = true
        ORDER BY pr.project_name
        """,
        params={"portfolio_id": portfolio_id},
        user_token=user_token,
    )
```

## Migration Steps

### Step 1: Update `query()` function

Uses `databricks-sql-connector` with per-user OBO token (not SDK `statement_execution`):

```python
from databricks import sql
from databricks.sdk.core import Config

cfg = Config()

def query(sql_str: str, params: dict = None, user_token: str = None) -> pd.DataFrame:
    """Execute a parameterized query as the current user."""
    if user_token is None:
        return _sample_data_fallback(sql_str)

    warehouse_id = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID")

    with sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{warehouse_id}",
        access_token=user_token,
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql_str, parameters=params)
            return cursor.fetchall_arrow().to_pandas()
```

**Note**: The old pattern used `StatementParameterListItem` from the SDK.
The SQL Connector uses standard DB-API parameterization with `:param_name`
syntax and a plain dict — simpler and consistent with our OBO auth approach.

### Step 2: Convert each function

Replace every f-string SQL with named parameters:

| Before | After |
|--------|-------|
| `f"WHERE id = '{my_id}'"` | `"WHERE id = :my_id"` + `params={"my_id": my_id}` |
| `f"WHERE status = '{status}'"` | `"WHERE status = :status"` + `params={"status": status}` |
| `f"VALUES ('{id}', '{name}')"` | `"VALUES (:id, :name)"` + `params={"id": id, "name": name}` |

### Step 3: Handle conditional WHERE clauses

```python
# Before (vulnerable)
where = f"WHERE r.portfolio_id = '{portfolio_id}'" if portfolio_id else ""
sql = f"SELECT * FROM risks {where}"

# After (safe)
params = {}
conditions = []
if portfolio_id:
    conditions.append("r.portfolio_id = :portfolio_id")
    params["portfolio_id"] = portfolio_id

where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
sql_str = f"SELECT * FROM risks {where}"
return query(sql_str, params=params, user_token=user_token)
```

### Step 4: Write operations (INSERT/UPDATE)

The cookbook's edit table recipe shows the parameterized write pattern:

```python
# Parameterized INSERT
def create_task(task_data: dict, user_token: str) -> None:
    sql_str = """
        INSERT INTO tasks (task_id, task_name, status, assigned_to)
        VALUES (:task_id, :task_name, :status, :assigned_to)
    """
    params = {
        "task_id": task_data["task_id"],
        "task_name": task_data["task_name"],
        "status": task_data.get("status", "not_started"),
        "assigned_to": task_data.get("assigned_to"),
    }
    execute_write(sql_str, params=params, user_token=user_token)

# Parameterized UPDATE with optimistic locking
def update_task_status(task_id: str, new_status: str, expected_updated_at: str, user_token: str) -> int:
    sql_str = """
        UPDATE tasks
        SET status = :new_status, updated_at = current_timestamp()
        WHERE task_id = :task_id AND updated_at = :expected_updated_at
    """
    params = {
        "task_id": task_id,
        "new_status": new_status,
        "expected_updated_at": expected_updated_at,
    }
    return execute_write(sql_str, params=params, user_token=user_token)
```

## Known Vulnerable Functions in data_access.py

These functions use f-string SQL and need migration:

| Function | Parameter(s) | Risk |
|----------|-------------|------|
| `get_portfolio_projects(portfolio_id)` | `portfolio_id` | HIGH |
| `get_project_detail(project_id)` | `project_id` | HIGH |
| `get_project_phases(project_id)` | `project_id` | HIGH |
| `get_project_charter(project_id)` | `project_id` | HIGH |
| `get_sprints(project_id)` | `project_id` | HIGH |
| `get_sprint_tasks(sprint_id)` | `sprint_id` | HIGH |
| `get_backlog(project_id)` | `project_id` | HIGH |
| `get_velocity(project_id)` | `project_id` | HIGH |
| `get_burndown(sprint_id)` | `sprint_id` | HIGH |
| `get_risks(portfolio_id)` | `portfolio_id` | HIGH |
| `get_resource_allocations(portfolio_id)` | `portfolio_id` | HIGH |
| `create_task(task_data)` | Multiple fields | CRITICAL |
| `update_task_status(task_id, new_status, ...)` | Multiple fields | CRITICAL |
| `move_task_to_sprint(task_id, sprint_id)` | Both params | CRITICAL |

Write operations (INSERT/UPDATE) are **CRITICAL** because they modify data.

## Grep Patterns to Find Violations

```bash
# F-string SQL with single-quoted variables
grep -rn "f['\"].*'{\|f['\"].*{.*}'.*SELECT\|INSERT\|UPDATE\|DELETE" utils/ repositories/

# String format in SQL
grep -rn "\.format(" utils/data_access.py repositories/

# String concatenation in SQL
grep -rn "sql.*+=" utils/ repositories/

# credentials_provider (service principal auth — should not be used)
grep -rn "credentials_provider" .

# WorkspaceClient statement_execution (wrong connection pattern)
grep -rn "statement_execution" .
```
