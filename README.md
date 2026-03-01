# PM Hub — Databricks Portfolio & Project Management App

## Architecture

```
Framework:    Dash (Plotly) — Python-native, rich visualization
Deployment:   Databricks Apps — OBO auth, serverless SQL
Data Layer:   Unity Catalog Delta tables — time travel, CDF
Schema:       Configurable via UC_CATALOG / UC_SCHEMA env vars (default: workspace.project_management)
```

## Why Dash (Not Streamlit, Not Flask)

| Requirement              | Streamlit | Flask/FastAPI | Dash (Plotly)  |
|--------------------------|-----------|---------------|----------------|
| Custom CSS/styling       | Limited   | Full          | Full           |
| Gantt charts             | Plugin    | Build custom  | Native Plotly  |
| Bubble charts            | Plotly    | Build custom  | Native         |
| Heatmaps                 | Plotly    | Build custom  | Native         |
| Kanban board             | No        | Build custom  | Callbacks      |
| State management         | Session   | Build custom  | Callbacks      |
| Team maintainability     | High      | Low (needs FE)| High (Python)  |
| Databricks Apps deploy   | Yes       | Yes           | Yes            |

**Dash is all Python, your team can maintain it, and Plotly handles 90% of
the visualization needs natively.**

## Project Structure

```
databricks-pm-app/
├── app.py                  # Main entry — layout, sidebar, routing
├── app.yaml                # Databricks Apps deployment config
├── requirements.txt        # Python dependencies
│
├── models/
│   └── schema_ddl.sql      # Full Unity Catalog DDL (17 tables)
│
├── pages/                  # Dash multi-page app — one file per view (16 pages)
│   ├── dashboard.py        # / — Portfolio KPIs, health, rollup
│   ├── portfolios.py       # /portfolios — Portfolio CRUD + budget burn charts
│   ├── roadmap.py          # /roadmap — Dependencies CRUD + cross-project mapping
│   ├── projects.py         # /projects — Project CRUD + health tracking + export
│   ├── charters.py         # /charters — Charter CRUD + approval workflow
│   ├── gantt.py            # /gantt — Phase/gate management + waterfall governance
│   ├── sprint.py           # /sprint — Kanban board + task CRUD
│   ├── my_work.py          # /my-work — Current user's assignments + edit
│   ├── backlog.py          # /backlog — Backlog management + task CRUD + export
│   ├── retros.py           # /retros — Retro CRUD + voting + convert-to-task
│   ├── reports.py          # /reports — Velocity, burndown, cycle time + export
│   ├── resources.py        # /resources — Team allocation + capacity planning + export
│   ├── risks.py            # /risks — PMI risk lifecycle + CRUD + heatmap + export
│   ├── deliverables.py     # /deliverables — Phase deliverables tracking
│   ├── comments.py         # /comments — Task comment threads
│   └── timesheet.py        # /timesheet — Time entry management
│
├── repositories/           # Data access — ALL SQL lives here
│   ├── base.py             # query(), write(), safe_update(), soft_delete()
│   ├── task_repo.py        # Task CRUD + status transitions
│   ├── sprint_repo.py      # Sprint CRUD + sprint tasks
│   ├── portfolio_repo.py   # Portfolio CRUD
│   ├── project_repo.py     # Project CRUD
│   ├── retro_repo.py       # Retro item CRUD + voting
│   └── ...                 # charter, risk, analytics, resource repos
│
├── services/               # Business logic — NO Dash imports
│   ├── task_service.py     # Task validation + orchestration
│   ├── sprint_service.py   # Sprint validation + orchestration
│   ├── charter_service.py  # Charter CRUD + approval workflow
│   ├── risk_service.py     # PMI risk lifecycle management
│   ├── retro_service.py    # Retro CRUD + voting + convert-to-task
│   ├── portfolio_service.py # Portfolio CRUD + dashboard aggregation
│   ├── project_service.py  # Project CRUD + detail retrieval
│   ├── auth_service.py     # OBO token, user identity, RBAC
│   ├── notification_service.py  # Real-time notification system
│   ├── export_service.py   # Excel export (openpyxl)
│   └── ...                 # analytics, audit, phase, deliverable, etc.
│
├── components/             # Reusable Dash UI components
│   ├── crud_modal.py       # CRUD modal factory (6 public functions)
│   ├── task_fields.py      # Shared TASK_FIELDS, SPRINT_FIELDS definitions
│   ├── toast.py            # Toast notification system
│   ├── department_selector.py  # Topbar department dropdown
│   ├── project_selector.py    # Topbar project context dropdown
│   ├── notification_bell.py   # Topbar notification bell + dropdown
│   ├── filter_bar.py       # Reusable filter bar + sort toggle
│   └── ...                 # kpi_card, empty_state, auto_refresh, etc.
│
├── charts/                 # Plotly figure builders
│   ├── theme.py            # COLORS dict, apply_theme()
│   └── ...                 # sprint, project, portfolio, analytics charts
│
├── callbacks/              # Cross-page Dash callbacks
│   ├── navigation.py       # Context-aware breadcrumbs
│   ├── department_callbacks.py  # Department selector state
│   ├── project_callbacks.py     # Project selector state
│   ├── notification_callbacks.py  # Notification bell updates
│   ├── state_callbacks.py  # URL-driven store updates
│   └── toast_callbacks.py  # Toast notification handler
│
├── utils/
│   ├── validators.py       # Input validation layer (11 validators, 7 composites)
│   ├── url_state.py        # URL query param helpers
│   └── labels.py           # Centralized user-facing strings
│
└── assets/                 # Dash auto-loads CSS/JS from here
    ├── custom.css          # Glassmorphism design system (~280 lines, 1800px fluid layout)
    ├── bootstrap-icons/    # Locally bundled Bootstrap Icons v1.11.3
    │   ├── bootstrap-icons.min.css
    │   └── fonts/          # WOFF2 + WOFF font files
    └── slate/              # Locally bundled Bootswatch SLATE theme
        └── bootstrap.min.css
```

## Schema Overview (18 Tables)

### Portfolio Layer
- **portfolios** — Strategic groupings (Data Platform, Financial Reporting, etc.)
- **dependencies** — Cross-project blocking relationships

### Project Layer
- **projects** — Individual projects with health, budget, delivery method
- **project_charters** — Formal charter documents (business case, scope, etc.)
- **project_team** — Team member assignments with allocation %

### Waterfall Layer
- **phases** — Sequential phases (Initiation → Design → Build → Test → Deploy)
- **gates** — Phase gate approvals (pending/approved/rejected)
- **deliverables** — Formal outputs per phase

### Agile Layer
- **sprints** — Time-boxed iterations (linked to phases in hybrid mode)
- **tasks** — Epics/stories/tasks/bugs/subtasks (hierarchical)
- **status_transitions** — Every status change (powers cycle time analytics)
- **retro_items** — Sprint retrospective items + action tracking

### Shared Layer
- **team_members** — People (synced from Databricks identity)
- **comments** — Task discussion threads
- **time_entries** — Hours logged per task
- **risks** — PMI risk register with probability × impact scoring, residual risk tracking, lifecycle management
- **notifications** — In-app notification system (task assignments, approvals, gate decisions)
- **audit_log** — Centralized audit trail for all entity changes

## Key Design Decisions

### Hybrid Waterfall + Agile in One Schema
The `phases` table handles waterfall structure. The `sprints` table handles agile.
The bridge is `sprints.phase_id` — in hybrid projects, sprints belong to a phase.
Tasks have both `phase_id` and `sprint_id`, so they can be viewed through either lens.

### Delta Time Travel for Burndown
Instead of building snapshot tables, we use Delta time travel:
```sql
SELECT * FROM tasks TIMESTAMP AS OF '2026-02-01'
WHERE sprint_id = 'sp-004'
```
This retroactively reconstructs the board state at any point in time.

### Change Data Feed for Audit
Tables with `'delta.enableChangeDataFeed' = 'true'` capture every row-level
change, powering the status_transitions and audit trail without triggers.

### OBO Authentication
Databricks Apps use on-behalf-of auth — the app runs as the logged-in user.
Unity Catalog row-level security and column masking apply automatically.
No separate auth system needed.

## Deployment

### 1. Create Schema
Run `models/schema_ddl.sql` in a Databricks notebook or SQL editor.

### 2. Seed Sample Data
(Optional) Run seed scripts to populate sample portfolios, projects, tasks.

### 3. Configure
Edit `app.yaml` with your SQL warehouse ID, catalog name, and schema name:
- `DATABRICKS_SQL_WAREHOUSE_ID` — your SQL warehouse ID
- `UC_CATALOG` — Unity Catalog catalog name (default: `workspace`)
- `UC_SCHEMA` — Unity Catalog schema name (default: `project_management`)

### 4. Deploy
```bash
databricks apps deploy pm-hub --source-code-path ./databricks-pm-app
```

### 5. Access
Your app will be available at:
`https://<workspace>.cloud.databricks.com/apps/pm-hub`

## Local Development
```bash
cd databricks-pm-app
pip install -r requirements.txt
USE_SAMPLE_DATA=true python app.py
# Opens at http://localhost:8050
# Uses in-memory sample data — full CRUD supported locally
```

## Reporting Queries

### Portfolio Health Summary
```sql
SELECT pf.name as portfolio,
       COUNT(*) as projects,
       SUM(CASE WHEN pr.health = 'green' THEN 1 ELSE 0 END) as on_track,
       SUM(CASE WHEN pr.health = 'yellow' THEN 1 ELSE 0 END) as at_risk,
       AVG(pr.pct_complete) as avg_completion,
       SUM(pr.budget_spent) / SUM(pr.budget_total) as burn_rate
FROM portfolios pf
JOIN projects pr ON pf.portfolio_id = pr.portfolio_id
WHERE pr.status = 'active'
GROUP BY pf.name
```

### Velocity Trend
```sql
SELECT s.name, s.start_date,
       SUM(CASE WHEN t.status = 'done' THEN t.story_points ELSE 0 END) as completed,
       s.capacity_points as committed
FROM sprints s
LEFT JOIN tasks t ON s.sprint_id = t.sprint_id
WHERE s.project_id = ? AND s.status = 'closed'
GROUP BY ALL ORDER BY s.start_date
```

### Cycle Time by Task Type
```sql
SELECT t.task_type,
       PERCENTILE(hours_in_status, 0.5) as median_hours,
       PERCENTILE(hours_in_status, 0.85) as p85_hours,
       AVG(hours_in_status) as avg_hours
FROM status_transitions st
JOIN tasks t ON st.task_id = t.task_id
WHERE st.from_status = 'in_progress'
  AND st.to_status IN ('review', 'done')
GROUP BY t.task_type
```

### Resource Over-Allocation
```sql
SELECT tm.display_name,
       SUM(pt.allocation_pct) as total_allocation,
       COUNT(DISTINCT pt.project_id) as project_count
FROM team_members tm
JOIN project_team pt ON tm.user_id = pt.user_id
WHERE tm.is_active = true
GROUP BY tm.display_name
HAVING SUM(pt.allocation_pct) > 100
ORDER BY total_allocation DESC
```
