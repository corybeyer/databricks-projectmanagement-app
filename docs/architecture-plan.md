# PM Hub — Architecture & Scaffolding Plan

> **Status (2026-02-26):** All 6 phases **complete**. The layered architecture
> (Pages → Services → Repositories → DB), repository pattern, sample data
> fallback, config layer, charts layer, and all 16 pages are built. All CRUD
> operations are fully interactive with validation, optimistic locking, and
> defense-in-depth patterns. Phase 5 (Production Readiness) added: Excel export,
> RBAC enforcement, Databricks-specific exception handling, 325 unit tests,
> and a real-time notification system. See [PLAN.md](architecture/PLAN.md)
> for the full roadmap history.

## Context

The Databricks PM Hub app is ~20% complete (2 of 13 pages) with a solid foundation but needs production-ready architecture before building further. The current structure (flat `utils/` with a 393-line `data_access.py` and 441-line `charts.py`) won't scale to 13 pages and 20-100 department users. Additionally, the app needs PostgreSQL integration alongside Unity Catalog — Postgres for OLTP/CRUD, Unity Catalog for analytics/reporting with Delta time travel.

This plan establishes the folder structure, design pattern, and scaffolding so all future development follows a consistent, extensible, production-grade pattern.

---

## Design Pattern: Pragmatic Layered Architecture with Repository Pattern

```
Presentation Layer    pages/ + components/ + callbacks/    UI layouts, callbacks
Service Layer         services/                            Business logic, orchestration
Repository Layer      repositories/                        Database queries
Infrastructure        config/ + db/                        Connections, config, caching
```

**Call direction (enforced):** Pages → Services → Repositories → DB. Never skip layers.

**Why this pattern:**
- MVC doesn't map well to Dash's reactive callbacks
- DDD is overkill for a 2-person team with well-understood domain (PMI PMBOK)
- The current partial layered approach (pages → utils) just needs to be completed and formalized

---

## Target Folder Structure

```
databricks-pm-app/
├── app.py                          # Entry point (layout shell, sidebar, server export)
├── app.yaml                        # Databricks Apps deployment config
├── requirements.txt                # Pinned dependencies
├── .env.example                    # Template for local env vars
├── CLAUDE.md                       # Updated project conventions
├── README.md
│
├── config/
│   ├── __init__.py                 # Exports get_settings()
│   ├── settings.py                 # Pydantic BaseSettings (env-driven)
│   └── logging.py                  # Structured logging config
│
├── db/
│   ├── __init__.py
│   ├── postgres.py                 # SQLAlchemy connection pool
│   ├── unity_catalog.py            # Databricks SDK connection
│   └── migrations/                 # Alembic migrations for Postgres
│       └── versions/
│
├── models/
│   ├── schema_ddl.sql              # Unity Catalog DDL (unchanged)
│   ├── postgres_ddl.sql            # PostgreSQL DDL (app state + CRUD tables)
│   └── sample_data.py              # Extracted from data_access._sample_data_fallback()
│
├── repositories/
│   ├── base.py                     # Query helpers, sample data switch, safe_update(), bulk_update()
│   ├── portfolio_repo.py           # get_portfolios(), get_portfolio_projects()
│   ├── project_repo.py             # get_project_detail(), get_project_phases()
│   ├── charter_repo.py             # get_project_charter(), create_charter()
│   ├── sprint_repo.py              # get_sprints(), get_sprint_tasks()
│   ├── task_repo.py                # Task CRUD, status transitions
│   ├── risk_repo.py                # get_risks(), create_risk()
│   ├── analytics_repo.py           # get_velocity(), get_burndown(), cycle times
│   ├── resource_repo.py            # get_resource_allocations(), get_team_members()
│   └── notification_repo.py        # Notification CRUD
│
├── services/
│   ├── portfolio_service.py        # KPI calculations, health rollups
│   ├── project_service.py          # Status logic, phase transitions
│   ├── sprint_service.py           # Sprint management, capacity
│   ├── task_service.py             # Task CRUD orchestration + transition logging
│   ├── analytics_service.py        # Report aggregation, caching coordination
│   ├── auth_service.py             # get_current_user(), has_permission() (placeholder)
│   ├── notification_service.py     # notify(), get_unread(), mark_read()
│   ├── audit_service.py            # log_action() — auto-called by all write operations
│   └── export_service.py           # to_excel(), to_pdf() (placeholder)
│
├── components/
│   ├── kpi_card.py                 # Reusable KPI card
│   ├── portfolio_card.py           # Portfolio summary card
│   ├── charter_display.py          # Charter document renderer
│   ├── charter_form.py             # Charter creation form
│   ├── task_card.py                # Kanban task card
│   ├── health_badge.py             # Status/health badge
│   ├── data_table.py               # Styled DataTable wrapper
│   ├── empty_state.py              # "No data" placeholder
│   ├── filters.py                  # Reusable filter dropdowns
│   ├── auto_refresh.py             # dcc.Interval (30s) + refresh-on-focus
│   ├── error_boundary.py           # Wraps sections for independent failure
│   ├── loading_wrapper.py          # dcc.Loading wrapper for data sections
│   └── export_button.py            # dcc.Download trigger
│
├── charts/
│   ├── __init__.py                 # Exports COLORS, apply_theme
│   ├── theme.py                    # COLORS dict, LAYOUT_DEFAULTS, apply_theme()
│   ├── portfolio_charts.py         # health_donut, budget_burn, strategic_bubble
│   ├── sprint_charts.py            # velocity, burndown
│   ├── project_charts.py           # gantt, roadmap
│   └── analytics_charts.py         # cycle_time, risk_heatmap, resource_utilization
│
├── pages/                          # 13 page files (layout only, no callbacks)
│   ├── dashboard.py                # /
│   ├── portfolios.py               # /portfolios
│   ├── roadmap.py                  # /roadmap
│   ├── projects.py                 # /projects
│   ├── charters.py                 # /charters
│   ├── gantt.py                    # /gantt
│   ├── sprint.py                   # /sprint
│   ├── my_work.py                  # /my-work
│   ├── backlog.py                  # /backlog
│   ├── retros.py                   # /retros
│   ├── reports.py                  # /reports
│   ├── resources.py                # /resources
│   └── risks.py                    # /risks
│
├── callbacks/
│   ├── __init__.py                 # Imports all callback modules for registration
│   ├── navigation.py               # Breadcrumb, sidebar state
│   ├── dashboard_callbacks.py      # Dashboard refresh, filters
│   ├── charter_callbacks.py        # Charter form submission
│   ├── sprint_callbacks.py         # Sprint board interactions
│   └── shared_callbacks.py         # Cross-page: project selector, notifications
│
├── utils/
│   ├── url_state.py                # URL query param read/write helpers (deep linking)
│   └── labels.py                   # All user-facing strings centralized
│
├── assets/
│   └── custom.css                  # Dash auto-loads
│
├── tests/
│   ├── conftest.py                 # Shared fixtures
│   ├── test_services/
│   ├── test_repositories/
│   ├── test_charts/
│   └── test_pages/                 # Smoke tests: layout() returns valid Div
│
├── scripts/
│   ├── init_postgres.py            # Create Postgres tables + seed
│   └── seed_sample_data.py         # Load sample data for dev
│
└── .github/
    └── workflows/
        └── deploy.yml              # CI: lint, test, deploy
```

---

## Data Split: PostgreSQL vs Unity Catalog

| Store | What lives there | Why |
|-------|-----------------|-----|
| **PostgreSQL** | All 17 CRUD tables (portfolios, projects, tasks, sprints, charters, risks, etc.) + user sessions/prefs + audit log | ACID transactions, sub-ms reads, proper UPDATE/DELETE, row-level locking |
| **Unity Catalog** | Analytics aggregations (velocity history, burndown snapshots, budget burn trends) | Delta time travel, governance/lineage, separated from OLTP load |
| **Both** | status_transitions | Write to Postgres (real-time), ETL to UC nightly for analytics |

A nightly Databricks Workflow ETL bridges Postgres → Unity Catalog for analytics data.

---

## Auth & Role Capability (Placeholder Pattern)

Build the skeleton now, enforce later. Every page and service will call auth functions that currently pass through.

- **`services/auth_service.py`**:
  - `get_current_user()` — reads identity from Databricks OBO SDK context (returns email/user_id)
  - `has_permission(user, required_level)` — **returns True for now** (placeholder)
  - `require_role(required_level)` — page-level guard wrapper, calls `has_permission()`
- **`roles` reference data** in Postgres: `role_name` + `permission_level` integer (admin=100, lead=80, member=50, viewer=20)
- **`team_members.role`** defaults to `'member'` for all users
- **Service methods** accept `current_user` parameter (ignored for now, ready for enforcement later)
- **Page layouts** call `require_role()` wrapper (passthrough for now)
- **Department scoping** deferred — add later when organizational structure is clearer

**When ready to enforce:** Change `has_permission()` from `return True` to actual role-check logic. No other files need to change.

---

## Concurrency: Optimistic Locking (Built In)

Every UPDATE in the repository base checks `updated_at` before writing:
```sql
UPDATE tasks SET ... WHERE task_id = :id AND updated_at = :expected_updated_at
```
If 0 rows affected → someone else changed it → return conflict error to the service layer → UI shows "This record was modified by another user. Please refresh."

Built into `repositories/base.py` as a reusable `safe_update()` method.

---

## Multi-User Protections (All Built Into Scaffolding)

### 1. Stale Data Prevention
- **`dcc.Interval`** (30s) as a standard pattern on all data-driven pages — not just dashboard
- **Refresh-on-focus**: clientside callback that triggers data reload when browser tab regains focus
- Add as a reusable component in `components/auto_refresh.py`

### 2. Optimistic Locking (Lost Update Prevention)
- Every mutable table has `updated_at` column (already in schema)
- `repositories/base.py` provides `safe_update(table, id, data, expected_updated_at)` method
- If 0 rows affected → raises `StaleDataError`
- Service layer catches `StaleDataError` → returns conflict result
- UI shows: "This record was modified by another user. Please refresh."

### 3. Transaction Wrappers (Race Condition Prevention)
- `db/postgres.py` provides a `transaction()` context manager
- Multi-step operations (close sprint, bulk status change) wrapped in transactions
- Service layer convention: any method that does 2+ writes uses `transaction()`
- Idempotent patterns: `UPDATE ... WHERE status = :expected_status` (second call finds 0 rows)

### 4. Long Query Isolation
- Analytics/reports pages use `dash.long_callback` with diskcache backend
- Heavy queries run in background process, show loading spinner, don't block connection pool
- Unity Catalog queries (historical analytics) separated from Postgres (CRUD) by design

### 5. Notifications (Placeholder — Table + Service, No UI Yet)
- **`notifications` table** in Postgres:
  - `notification_id`, `user_email`, `type` (assignment, status_change, comment, mention)
  - `title`, `message`, `entity_type`, `entity_id`
  - `is_read` (boolean), `created_at`
- **`services/notification_service.py`**:
  - `notify(user_email, type, title, message, entity_type, entity_id)` — creates DB record
  - `get_unread(user_email)` — returns unread notifications
  - `mark_read(notification_id)` — marks as read
- Service methods call `notification_service.notify()` on key events (task assignment, sprint close, comment added)
- **UI deferred** — notification bell/badge added later. The data pipeline is ready.

---

## Additional Architectural Safeguards

### 6. Schema Evolution Strategy
- Every Alembic migration has `upgrade()` AND `downgrade()` (rollback capability)
- Data migrations (value transforms, not just DDL) follow same pattern
- Unity Catalog migrations: `db/migrations/unity_catalog/` with numbered SQL files (001_initial.sql, etc.)
- Convention in CLAUDE.md: never modify existing migration files, always create new ones

### 7. Audit Trail (Consistent, Automatic)
- `services/audit_service.py` — `log_action(user, action, entity_type, entity_id, details)` writes to `app_audit_log`
- Every service write method calls `audit_service.log_action()` automatically
- **Soft deletes** as default convention: all mutable tables have `is_deleted BOOLEAN DEFAULT false` + `deleted_at TIMESTAMP`
- Queries filter `WHERE is_deleted = false` by default; repos provide `include_deleted=False` parameter for admin views
- Answers "who changed what, when?" for any record

### 8. Error Boundaries & Graceful Degradation
- `components/error_boundary.py` — wraps page sections independently so partial failures don't crash the whole page
- Pattern: each KPI card, chart, and data section wrapped individually
- If Postgres unreachable: fall back to cached data + show "Data may be stale" banner (not full error page)
- `components/loading_wrapper.py` — every data-loading section gets `dcc.Loading` (prevents duplicate clicks)

### 9. URL State & Deep Linking
- `utils/url_state.py` — helpers to read/write URL query params via `dcc.Location`
- Convention: all filter/selection state stored in URL (not just `dcc.Store`)
- Enables: bookmarkable views, shareable links (`/sprint?project=abc&sprint=3`), browser back/forward
- Every page reads initial state from URL on load

### 10. Bulk Operations
- `repositories/base.py` provides `bulk_update(table, ids, data)` wrapped in transaction
- Service layer exposes bulk methods: `task_service.bulk_update_status(task_ids, new_status, user)`
- UI can use single operations initially; bulk UI added later without service changes

### 11. Export / Reporting
- `services/export_service.py` — placeholder with `to_excel(df, filename)`, `to_pdf(content)` signatures
- `components/export_button.py` — reusable download trigger using `dcc.Download`
- Convention: export buttons appear in page header area, consistent placement

### 12. Feature Flags
- `config/settings.py` includes `feature_flags: dict` for toggling pages/features
- `app.py` sidebar checks flags before rendering nav links
- Pages check flags before registering routes
- Enables incremental deployment: ship half-built pages hidden behind flags

### 13. String Centralization
- `utils/labels.py` — all user-facing strings as constants (page titles, button labels, error messages, status display names)
- Convention: pages/components import from `labels.py`, never hard-code user-facing text
- Not full i18n, just centralization for consistency and future-proofing

### 14. Service Layer Isolation Rule
- **Services NEVER import from Dash** (no `html`, `dbc`, `dcc`, `dash`)
- Services accept/return pure Python types (dicts, DataFrames, strings)
- This makes services reusable as a future API layer (REST/FastAPI, Slack bot, notebook)

### 15. Dash-Specific Conventions (Avoid Common Mistakes)
- **ID namespacing**: all component IDs prefixed with page name (`dashboard-kpi-cards`, `sprint-task-list`)
- **No circular callbacks**: callbacks never trigger themselves; document callback chains
- **Max ~10 callbacks per page**: split into sub-components if more needed
- **`dcc.Store` for IDs/filters only**: never store full DataFrames in browser; fetch server-side
- **CSS classes over inline styles**: use `className`, not `style={}` (except dynamic values like colors)
- **`dcc.Loading` on every data section**: prevents duplicate clicks, shows progress

---

## Key Infrastructure Decisions

### Configuration
- **Pydantic `BaseSettings`** in `config/settings.py` — type-safe, reads from `.env` locally and `app.yaml` env vars in Databricks
- `.env.example` committed, `.env` gitignored

### Connection Management
- **Postgres**: SQLAlchemy engine with pool (pool_size=5, max_overflow=10)
- **Unity Catalog**: Databricks SDK `WorkspaceClient` (existing pattern, refined)
- **Local dev**: `USE_SAMPLE_DATA=true` flag returns mock data from `models/sample_data.py`

### Caching
- `flask-caching` with `SimpleCache` (in-memory, single process)
- Dashboard/portfolio: 5-min TTL; Sprint/task: 2-min TTL; Analytics: 15-min TTL
- Service layer handles cache invalidation after writes

### Error Handling
- Repos: catch DB exceptions, log, raise typed errors
- Services: catch repo errors, provide fallbacks
- Callbacks: try/except returning `dbc.Alert` on failure — never show tracebacks

### SQL Safety
- **Postgres**: Parameterized queries with `:param_name` syntax (SQLAlchemy `text()`) — never f-strings with user input
- **Unity Catalog**: Use SDK `parameters` argument

### Testing
- Unit: services with mocked repos, chart builders, component rendering
- Integration: repo queries against test Postgres
- Smoke: every `layout()` returns valid `html.Div`, app starts without error

---

## Migration Path (Implementation Order)

**Approach: Scaffolding first, clean cut migration (no deprecated wrappers).**

All new structure is built, existing code is migrated, old `utils/` is deleted, and imports are updated in one pass. This keeps the codebase clean — no dual paths.

### Step 1: Local Postgres setup
- Install Postgres via Docker (recommended):
  ```
  docker run --name pmhub-postgres -e POSTGRES_DB=pm_hub -e POSTGRES_USER=pm_hub -e POSTGRES_PASSWORD=localdev -p 5432:5432 -d postgres:16
  ```
- Alternative: Native install via https://www.postgresql.org/download/windows/
- Create `.env` with connection string

### Step 2: Foundation scaffolding
Create all directories and `__init__.py` files:
- `config/`, `db/`, `db/migrations/`, `db/migrations/unity_catalog/`, `repositories/`, `services/`, `components/`, `charts/`, `callbacks/`, `utils/`, `tests/`, `scripts/`
- Create `config/settings.py` (Pydantic BaseSettings with Postgres + Databricks config + **feature_flags dict**)
- Create `config/logging.py`
- Create `.env.example` with all required env vars documented
- Create `utils/url_state.py` (URL query param read/write helpers)
- Create `utils/labels.py` (centralized user-facing strings)
- Add `pydantic-settings`, `psycopg2-binary`, `sqlalchemy`, `flask-caching`, `dash-diskcache` to `requirements.txt`

### Step 3: Database layer
- Create `db/postgres.py` — SQLAlchemy engine with connection pool + `transaction()` context manager
- Create `db/unity_catalog.py` — Databricks SDK connection (extracted from `data_access.py`)
- Create `models/postgres_ddl.sql` — Postgres-adapted schema + app tables:
  - `user_sessions`, `user_preferences`, `app_audit_log` (app state)
  - `notifications` table (user_email, type, title, message, entity_type, entity_id, is_read, created_at)
  - `roles` reference table (role_name, permission_level)
- Create `scripts/init_postgres.py` — Run DDL and seed sample data + roles

### Step 4: Decompose `utils/data_access.py` (clean cut)
- Extract `_sample_data_fallback()` → `models/sample_data.py`
- Create `repositories/base.py` with:
  - Shared query infrastructure + sample data switch
  - `safe_update()` with optimistic locking (`updated_at` check)
  - `bulk_update()` wrapped in transaction
  - Default `WHERE is_deleted = false` filter with `include_deleted` param
- Split 25+ query functions into domain repositories:
  - `portfolio_repo.py`, `project_repo.py`, `charter_repo.py`, `sprint_repo.py`
  - `task_repo.py`, `risk_repo.py`, `analytics_repo.py`, `resource_repo.py`, `notification_repo.py`
- **Delete `utils/data_access.py`**

### Step 5: Split `utils/charts.py` (clean cut)
- Extract `COLORS`, `LAYOUT_DEFAULTS`, `apply_theme()` → `charts/theme.py`
- Group chart functions: `portfolio_charts.py`, `sprint_charts.py`, `project_charts.py`, `analytics_charts.py`
- **Delete `utils/charts.py`**

### Step 6: Extract components from existing pages
- `kpi_card()`, `portfolio_card()` from `dashboard.py` → `components/kpi_card.py`, `components/portfolio_card.py`
- `charter_section()`, `charter_display()`, `charter_form()` from `charters.py` → `components/`

### Step 7: Create auth + notification services (placeholder patterns)
- `services/auth_service.py` — `get_current_user()`, `has_permission()` (returns True for now), `require_role()` (page guard)
- `services/notification_service.py` — `notify()`, `get_unread()`, `mark_read()` (writes to notifications table, no UI yet)
- Wire `require_role()` into existing page layouts (passthrough)

### Step 8: Create all services + multi-user infrastructure
- `services/portfolio_service.py` — KPI calculations (used by dashboard)
- `services/project_service.py` — Charter retrieval logic (used by charters page)
- `services/audit_service.py` — `log_action()`, auto-called by all write operations
- `services/export_service.py` — `to_excel()`, `to_pdf()` placeholders
- `components/auto_refresh.py` — Reusable `dcc.Interval` (30s) + refresh-on-focus
- `components/error_boundary.py` — Independent section failure handling
- `components/loading_wrapper.py` — `dcc.Loading` wrapper for data sections
- `components/export_button.py` — `dcc.Download` trigger

### Step 9: Extract callbacks
- Move `update_breadcrumb()` from `app.py` → `callbacks/navigation.py`
- Extract dashboard callbacks → `callbacks/dashboard_callbacks.py`
- Extract charter callbacks → `callbacks/charter_callbacks.py`
- Create `callbacks/__init__.py` that imports all modules for registration

### Step 10: Update all imports — `app.py`, `dashboard.py`, `charters.py`
Update to use new paths. **Delete `utils/` directory entirely.**

### Step 11: Update `CLAUDE.md` with new conventions
Add layer rules, repository/service/component/callback conventions, auth patterns, new "What NOT To Do" entries.

### Step 12: Set up tests
- Create `tests/conftest.py` with fixtures (sample DataFrames, mock repos)
- Smoke tests: every `layout()` returns valid `html.Div`
- Chart tests: every chart builder returns `go.Figure` without error
- `test_app_startup.py`: app initializes without error

### Step 13: Verify
- `python app.py` starts without errors
- Dashboard (`/`) loads with sample data
- Charters (`/charters`) loads with sample data
- All imports resolve (no circular dependencies)
- `pytest tests/` passes

---

## CLAUDE.md Additions (New Conventions)

Key rules to add:
- **Layer call direction**: Pages → Services → Repositories → DB (never skip)
- **Repository convention**: One file per domain, returns pd.DataFrame, parameterized queries only, soft delete default
- **Service convention**: Business logic only, handles cache invalidation, calls audit_service on writes, **NEVER imports from Dash**
- **Component convention**: Pure functions (data in, Dash component out), never import services
- **Callback convention**: Lives in `callbacks/`, calls services not repos, try/except with dbc.Alert
- **Config convention**: Always use `config/settings.py`, never `os.getenv()` directly
- **ID namespacing**: All Dash component IDs prefixed with page name (`dashboard-kpi-cards`)
- **URL state**: Filter/selection state stored in URL query params (bookmarkable, shareable)
- **Strings**: All user-facing text imported from `utils/labels.py`, never hard-coded in pages
- **Loading states**: Every data-loading section wrapped in `dcc.Loading`
- **Error boundaries**: Each page section handles errors independently (partial failure, not full page crash)
- **Feature flags**: New pages/features gated in `config/settings.py` feature_flags dict
- **Migrations**: Every migration has upgrade() + downgrade(); never modify existing migrations
- **Soft deletes**: `is_deleted` + `deleted_at` on mutable tables; hard delete only for truly transient data
- **Max callbacks**: ~10 per page; split into sub-components if more needed
- **No circular callbacks**: Callbacks never trigger themselves

---

## Verification

After scaffolding is complete:
1. `python app.py` starts without errors
2. Dashboard (`/`) loads with sample data
3. Charters (`/charters`) loads with sample data
4. All imports resolve (no circular dependencies)
5. `pytest tests/` passes smoke tests
