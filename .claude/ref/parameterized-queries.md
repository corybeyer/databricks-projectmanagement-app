# Parameterized Queries — Migration Guide

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
def get_portfolio_projects(portfolio_id: str) -> pd.DataFrame:
    return query(
        """
        SELECT pr.*, ph.name as current_phase_name
        FROM projects pr
        LEFT JOIN phases ph ON pr.current_phase_id = ph.phase_id
        WHERE pr.portfolio_id = :portfolio_id
        AND pr.is_active = true
        ORDER BY pr.project_name
        """,
        params={"portfolio_id": portfolio_id}
    )
```

## Migration Steps

### Step 1: Update `query()` function
```python
from databricks.sdk.service.sql import StatementParameterListItem

def query(sql: str, params: dict = None) -> pd.DataFrame:
    client = _get_sql_connection()
    if client is None:
        return _sample_data_fallback(sql)

    warehouse_id = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID")

    # Build parameter list for SDK
    parameters = None
    if params:
        parameters = [
            StatementParameterListItem(name=k, value=str(v), type="STRING")
            for k, v in params.items()
        ]

    result = client.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql,
        catalog=CATALOG,
        schema=SCHEMA,
        parameters=parameters,
    )
    # ... rest of result handling
```

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
sql = f"SELECT * FROM risks {where}"
return query(sql, params=params)
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
grep -rn "\.format(" utils/data_access.py

# String concatenation in SQL
grep -rn "sql.*+=" utils/ repositories/
```
