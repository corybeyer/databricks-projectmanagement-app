---
name: new-table
description: Generate Unity Catalog DDL for a new table following PM Hub schema conventions. Creates the DDL, adds it to schema_ddl.sql, and creates a numbered migration script.
arguments:
  - name: name
    description: "Table name (plural, lowercase, underscores — e.g., milestones)"
    required: true
  - name: description
    description: "Brief description of what the table stores"
    required: true
---

Generate a new Unity Catalog Delta table following PM Hub conventions.

## Steps

1. Validate table name:
   - Lowercase with underscores
   - Plural form
   - Not already in schema_ddl.sql

2. Determine the next migration number by checking `models/migrations/` for existing files.

3. Generate the DDL following these conventions:
   - Primary key: `{singular}_id STRING NOT NULL`
   - Include relevant foreign keys to existing tables
   - Add `created_at TIMESTAMP NOT NULL DEFAULT current_timestamp()`
   - Add `updated_at TIMESTAMP` if the table is mutable
   - Add COMMENT on every column
   - Add table-level COMMENT
   - Set `'delta.enableChangeDataFeed' = 'true'` if audit tracking is needed
   - Add PRIMARY KEY and FOREIGN KEY constraints

4. Ask the user what columns the table needs (beyond the standard ones).

5. Create two files:
   - Append DDL to `models/schema_ddl.sql`
   - Create `models/migrations/{NNN}_add_{table_name}.sql` with the DDL

6. Add a stub query function to `utils/data_access.py`:
   ```python
   def get_{table_name}() -> pd.DataFrame:
       return query("SELECT * FROM {table_name}")
   ```

7. Report what was created.

## Column Type Reference

| Use Case | Type | Example |
|----------|------|---------|
| Identifiers | STRING | project_id, sprint_id |
| Names, text | STRING | name, description, body |
| Status enums | STRING | status, priority, category |
| Whole numbers | INT | story_points, votes, capacity |
| Decimals | DOUBLE | hours, allocation_pct, backlog_rank |
| Yes/no | BOOLEAN | is_active, is_archived |
| Calendar dates | DATE | start_date, due_date |
| Precise timestamps | TIMESTAMP | created_at, transitioned_at |

## Example

```
/new-table milestones "Key project milestones with target and actual dates"
```

Generates:
```sql
CREATE TABLE IF NOT EXISTS milestones (
    milestone_id    STRING      NOT NULL    COMMENT 'PK — UUID',
    project_id      STRING      NOT NULL    COMMENT 'FK → projects',
    name            STRING      NOT NULL    COMMENT 'Milestone name',
    ...
);
```
