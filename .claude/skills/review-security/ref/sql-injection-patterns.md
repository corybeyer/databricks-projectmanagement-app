# SQL Injection Patterns — PM Hub

## Known Vulnerable Pattern

PM Hub uses f-string interpolation for SQL queries throughout `utils/data_access.py`. The general pattern:

```python
def get_something(param: str) -> pd.DataFrame:
    return query(f"""
        SELECT * FROM table
        WHERE column = '{param}'
    """)
```

## Attack Scenarios

### 1. Classic SQL Injection via ID Parameter
If `portfolio_id` comes from a URL parameter or callback input:
```python
# User passes: ' OR '1'='1
# Resulting SQL:
SELECT * FROM projects WHERE portfolio_id = '' OR '1'='1'
# Returns ALL projects, bypassing access control
```

### 2. UNION-based Data Extraction
```python
# User passes: ' UNION SELECT token, secret, null FROM credentials --
# Resulting SQL:
SELECT * FROM projects WHERE portfolio_id = '' UNION SELECT token, secret, null FROM credentials --'
```

### 3. Write Operation Injection
Write operations (INSERT, UPDATE) are especially dangerous:
```python
# In create_task(), if task_data fields are user-controlled:
# User passes task_name: '); DROP TABLE projects; --
# Resulting SQL:
INSERT INTO tasks (task_name) VALUES (''); DROP TABLE projects; --')
```

### 4. Conditional WHERE Clause Injection
```python
# The pattern:
where = f"WHERE r.portfolio_id = '{portfolio_id}'" if portfolio_id else ""
# If portfolio_id = "' OR 1=1 --"
# Resulting WHERE: WHERE r.portfolio_id = '' OR 1=1 --'
```

## Grep Patterns to Detect

```bash
# F-string with SQL keywords
grep -rn "f['\"].*SELECT" utils/ repositories/ pages/
grep -rn "f['\"].*INSERT" utils/ repositories/ pages/
grep -rn "f['\"].*UPDATE" utils/ repositories/ pages/
grep -rn "f['\"].*DELETE" utils/ repositories/ pages/

# Variable interpolation inside quoted SQL values
grep -rn "'{[a-zA-Z_]*}'" utils/ repositories/

# .format() on SQL strings
grep -rn "\.format(.*)" utils/data_access.py

# String concatenation with SQL
grep -rn "sql.*+=" utils/ repositories/
grep -rn "sql = sql \+" utils/ repositories/
```

## Mitigating Context

In PM Hub's current architecture:
- Queries execute inside **Unity Catalog auth context** (Databricks SDK)
- The app runs as a **Databricks App** with OBO auth
- User input flows through Dash callbacks (somewhat constrained)

However, these mitigations are **defense-in-depth, not a fix**:
- Unity Catalog doesn't prevent SQL injection — it prevents unauthorized table access
- OBO auth means injected queries run with the user's permissions
- Dash callbacks can receive arbitrary string input via URL parameters

## Severity Assessment

| Category | Severity | Rationale |
|----------|----------|-----------|
| Read operations with f-string params | HIGH | Data exfiltration possible within user's permissions |
| Write operations with f-string params | CRITICAL | Data modification, potential data loss |
| Conditional WHERE clauses | HIGH | Can bypass intended filtering |
| Functions with no parameters | LOW | No injection vector (e.g., `get_portfolios()`) |
