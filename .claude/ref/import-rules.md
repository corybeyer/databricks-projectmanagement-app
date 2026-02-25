# Import Rules — Grep Patterns for Violation Detection

## Layer Violation Detection

### Pages must NOT import from repositories or db
```bash
# Check pages/ for direct repository imports
grep -rn "from repositories" pages/
grep -rn "import repositories" pages/
grep -rn "from db" pages/
grep -rn "import db" pages/

# Check pages/ for direct database imports
grep -rn "from databricks" pages/
grep -rn "import sqlalchemy" pages/
```

### Services must NOT import from presentation layer
```bash
# Check services/ for page/UI imports
grep -rn "from pages" services/
grep -rn "import pages" services/
grep -rn "from components" services/
grep -rn "from callbacks" services/
grep -rn "import dash" services/
grep -rn "from dash" services/
grep -rn "import plotly" services/
grep -rn "from plotly" services/
```

### Repositories must NOT import from services or pages
```bash
grep -rn "from services" repositories/
grep -rn "import services" repositories/
grep -rn "from pages" repositories/
grep -rn "import pages" repositories/
```

## SQL Placement Violations

### SQL must NOT appear in pages or services
```bash
# SQL keywords in page files
grep -rn "SELECT\s" pages/ --include="*.py"
grep -rn "INSERT\s" pages/ --include="*.py"
grep -rn "UPDATE\s" pages/ --include="*.py"
grep -rn "DELETE\s" pages/ --include="*.py"
grep -rn "CREATE TABLE" pages/ --include="*.py"

# SQL keywords in service files
grep -rn "SELECT\s" services/ --include="*.py"
grep -rn "INSERT\s" services/ --include="*.py"
grep -rn "UPDATE\s" services/ --include="*.py"
grep -rn "DELETE\s" services/ --include="*.py"

# SQL keywords in callback files
grep -rn "SELECT\s" callbacks/ --include="*.py"
grep -rn "INSERT\s" callbacks/ --include="*.py"
```

## Naming Convention Checks

### Primary key naming: {singular}_id
```bash
# Find all _id columns in schema DDL
grep -n "_id\s" models/schema_ddl.sql

# Find primary key declarations
grep -n "PRIMARY KEY" models/schema_ddl.sql
```

### Table naming: lowercase, plural, underscores
```bash
# Find CREATE TABLE statements
grep -n "CREATE TABLE" models/schema_ddl.sql

# Check for camelCase or PascalCase table names (violation)
grep -n "CREATE TABLE.*[A-Z]" models/schema_ddl.sql
```

### File naming: snake_case
```bash
# Find Python files with non-snake_case names
find pages/ services/ repositories/ utils/ -name "*.py" | grep -v "^[a-z_/]*\.py$"
```

## Schema Convention Checks

### Every table must have created_at
```bash
# Find tables and check for created_at
# Compare CREATE TABLE count vs created_at count
grep -c "CREATE TABLE" models/schema_ddl.sql
grep -c "created_at" models/schema_ddl.sql
```

### Mutable tables must have updated_at
```bash
grep -c "updated_at" models/schema_ddl.sql
```

### Delta format verification
```bash
grep -n "USING DELTA\|TBLPROPERTIES" models/schema_ddl.sql
```

### Change data feed for audited tables
```bash
grep -n "enableChangeDataFeed" models/schema_ddl.sql
```

## Circular Import Detection

```bash
# Find potential circular import chains
# pages → utils → pages (if utils imports from pages)
grep -rn "from pages" utils/
grep -rn "import pages" utils/

# utils → utils cross-module
grep -rn "from utils.charts" utils/data_access.py
grep -rn "from utils.data_access" utils/charts.py
```

## Running All Checks

To run a comprehensive check, execute each section above. The review agent reads these patterns and applies them automatically during `/review-architecture`.
