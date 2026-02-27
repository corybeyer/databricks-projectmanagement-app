# CLAUDE.md — PM Hub Project Intelligence

> Claude reads this file automatically at the start of every session.
> Last updated: 2026-02-26 | Current Phase: 5 (Production Roadmap)

## Environment

This project runs on Windows with Git Bash. Avoid shell commands that depend
on Linux-only tools (e.g., jq). Use Python for JSON parsing instead of jq.
Test all hook scripts for Git Bash compatibility before committing.

## Project Identity

**PM Hub** is a portfolio and project management application built on Databricks.
It supports hybrid waterfall/agile project delivery following PMI PMBOK 7 principles.
The app is built with Dash (Plotly), deployed as a Databricks App, and backed by
Unity Catalog Delta tables.

- **Repo**: `corybeyer/databricks-projectmanagement-app`
- **Framework**: Dash (Plotly) with Dash Bootstrap Components
- **Deployment**: Databricks Apps (app.yaml config)
- **Data Layer**: Unity Catalog — `workspace.project_management` schema
- **CI/CD**: GitHub Actions → Databricks CLI deploy on push to main

## Team & Roles

- **Cory S.** — Data Engineering Manager, PM, primary developer
- **Claude** — AI-assisted development partner
- Team works primarily in Python and SQL. No dedicated frontend developers.
  All UI must be maintainable by data engineers.

## Architecture Plan

See [docs/architecture-plan.md](docs/architecture-plan.md) for the scaffolding & architecture plan.
See [docs/architecture/PLAN.md](docs/architecture/PLAN.md) for the production roadmap (Phase 0–5).
**Current step**: Phase 5 — Polish & Production Readiness (Phase 4 fully complete)
**Pattern**: Pragmatic Layered Architecture with Repository Pattern
**Call direction**: Pages → Services → Repositories → DB (never skip layers)

## Current State

- **Phase**: 5 — Production Roadmap (Schema → Foundation → CRUD → Navigation → PMI → Polish)
- **Roadmap**: See [docs/architecture/PLAN.md](docs/architecture/PLAN.md) — 32 tasks across 6 phases
- **Current Work**: Phase 5 — Polish & Production Readiness
- **Phase 0 Done**: Departments, user tracking, PMI risks, audit log, schema fixes (PR #19)
- **Phase 1 Done**: Toast system, auto-refresh (13 pages), validation layer, dcc.Store state, error boundaries, change history (PR #20)
- **Phase 2 Prereqs Done**: In-memory write mode, CRUD modal component, task_fields (PR #22)
- **Phase 2a Done**: Task CRUD + kanban, sprint management, backlog CRUD, my-work edit (PR #23)
- **Phase 2b.3 Done**: Charter CRUD + approval workflow (PR #24)
- **Phase 2b.4 Done**: PMI Risk Management full lifecycle (PR #24)
- **Phase 2b.5 Done**: Retrospective CRUD + voting, sprint selector, convert-to-task (PR #26)
- **Phase 2b.6 Done**: Project & Portfolio CRUD + validate_portfolio_create (PR #26)
- **Phase 3 Done**: Dept/project selectors, drill-down hierarchy, filter bars, sort toggles, context-aware breadcrumbs (PR #27)
- **Phase 4 Done**: Phase/gate management, deliverables tracking, dependencies view, comments, time tracking, resource management enhancements (PR #29)
- **Pages**: 16/16 built (13 original + 3 new: deliverables, comments, timesheet); all CRUD pages fully interactive
- **Blockers**: None
- **Next Gate**: Phase 5 Polish & Production Readiness

## Architecture Rules

### Layered Architecture — Call Direction

```
Pages (UI) → Services (logic) → Repositories (data) → DB (connection)
```

- **Pages** import from services, components, and charts. Never from repositories or db.
- **Services** import from repositories. Never import Dash. Accept/return pure Python types.
- **Repositories** import from db. Return `pd.DataFrame`. All SQL lives here.
- **DB** manages connections (Unity Catalog via OBO auth). No business logic.

### File Structure

```
databricks-pm-app/
├── app.py                  # Entry point — imports callbacks, reads config
├── app.yaml                # Databricks Apps config
├── requirements.txt        # Pin versions. Always.
├── .env.example            # Template for local dev env vars
├── config/
│   ├── __init__.py         # Exports get_settings()
│   ├── settings.py         # Pydantic BaseSettings (env vars)
│   └── logging.py          # Structured logging setup
├── db/
│   ├── __init__.py
│   ├── unity_catalog.py    # OBO auth connection, execute_query/write
│   └── postgres.py         # Placeholder (future)
├── models/
│   ├── schema_ddl.sql      # Single source of truth for table definitions
│   ├── sample_data.py      # Sample data for local dev fallback
│   └── migrations/         # Numbered migration scripts (001_, 002_)
├── repositories/           # Data access — ALL SQL lives here
│   ├── base.py             # query(), write(), safe_update()
│   ├── portfolio_repo.py
│   ├── project_repo.py
│   ├── charter_repo.py
│   ├── sprint_repo.py
│   ├── task_repo.py
│   ├── risk_repo.py
│   ├── analytics_repo.py
│   ├── resource_repo.py
│   ├── phase_repo.py
│   ├── gate_repo.py
│   ├── deliverable_repo.py
│   ├── dependency_repo.py
│   ├── comment_repo.py
│   └── time_entry_repo.py
├── services/               # Business logic — NO Dash imports
│   ├── auth_service.py     # OBO token, user identity, permissions
│   ├── portfolio_service.py
│   ├── project_service.py
│   ├── sprint_service.py
│   ├── task_service.py
│   ├── analytics_service.py
│   ├── phase_service.py
│   ├── deliverable_service.py
│   ├── dependency_service.py
│   ├── comment_service.py
│   ├── time_entry_service.py
│   ├── resource_service.py
│   ├── audit_service.py    # Placeholder
│   ├── notification_service.py  # Placeholder
│   └── export_service.py   # Placeholder
├── charts/                 # Plotly figure builders
│   ├── __init__.py         # Exports COLORS, apply_theme
│   ├── theme.py            # COLORS, LAYOUT_DEFAULTS, apply_theme()
│   ├── portfolio_charts.py
│   ├── sprint_charts.py
│   ├── project_charts.py
│   └── analytics_charts.py
├── components/             # Reusable Dash UI components
│   ├── kpi_card.py
│   ├── portfolio_card.py
│   ├── charter_display.py
│   ├── charter_form.py
│   ├── health_badge.py
│   ├── empty_state.py
│   ├── loading_wrapper.py
│   ├── auto_refresh.py
│   ├── error_boundary.py
│   ├── export_button.py
│   └── comment_thread.py
├── callbacks/              # Dash callbacks (separate from pages)
│   ├── __init__.py         # Imports all callback modules
│   └── navigation.py       # Breadcrumb callback
├── pages/                  # One file per route (16/16 complete)
│   ├── dashboard.py        # /
│   ├── portfolios.py       # /portfolios
│   ├── roadmap.py          # /roadmap
│   ├── projects.py         # /projects
│   ├── charters.py         # /charters
│   ├── gantt.py            # /gantt
│   ├── sprint.py           # /sprint
│   ├── my_work.py          # /my-work
│   ├── backlog.py          # /backlog
│   ├── retros.py           # /retros
│   ├── reports.py          # /reports
│   ├── resources.py        # /resources
│   ├── risks.py            # /risks
│   ├── deliverables.py     # /deliverables
│   ├── comments.py         # /comments
│   └── timesheet.py        # /timesheet
├── utils/
│   ├── url_state.py        # URL query param helpers
│   └── labels.py           # Centralized user-facing strings
├── assets/                 # Dash auto-loads (custom.css)
└── tests/
    ├── conftest.py
    ├── test_pages/
    └── test_charts/
```

### Layer Rules

**Pages** — Every page file must:
1. Register with `dash.register_page(__name__, path="/route")`
2. Define a `layout()` function (not a variable)
3. Import data from `services/` — never write SQL or call repositories
4. Import chart builders from `charts/` — never build figures inline
5. Import UI pieces from `components/` — extract reusable parts
6. Use Dash Bootstrap Components for layout (dbc.Row, dbc.Col, dbc.Card)

**Services** — `services/` rules:
1. Never import Dash (`dash`, `dbc`, `dcc`, `html`)
2. Accept and return pure Python types (dicts, lists, DataFrames)
3. Call repositories for data access
4. Contain business logic, KPI calculations, orchestration

**Repositories** — `repositories/` rules:
1. Every query is a named function: `get_portfolios()`, `get_sprint_tasks(sprint_id)`
2. Functions return `pd.DataFrame` always
3. All SQL uses parameterized queries (`:param_name` with `parameters={}` dict)
4. **Never** use f-strings for SQL — this is a security rule
5. Every function has a sample data fallback via `@query` decorator
6. `safe_update()` uses optimistic locking via `updated_at`
7. All queries include `WHERE is_deleted = false` by default

**Charts** — `charts/` rules:
1. Every chart function takes a DataFrame and returns a `go.Figure`
2. All figures call `apply_theme(fig)` before returning
3. Color constants live in `charts/theme.py` COLORS dict
4. Never hardcode colors inside chart functions

**Components** — `components/` rules:
1. Each file exports one or more functions returning Dash components
2. Functions accept simple arguments (strings, dicts, DataFrames)
3. Reusable across pages

**Schema** — Unity Catalog conventions:
1. Table names: lowercase, underscores, plural (`projects`, `team_members`)
2. Primary keys: `{singular}_id` as STRING (UUID)
3. Foreign keys: match the referenced table's PK name exactly
4. Every table has `created_at TIMESTAMP NOT NULL DEFAULT current_timestamp()`
5. Mutable tables also have `updated_at TIMESTAMP`
6. Status columns use lowercase snake_case enums: `active`, `in_progress`, `not_started`
7. All tables are Delta format with time travel enabled
8. Tables with audit needs have `'delta.enableChangeDataFeed' = 'true'`

### Styling

- Dark theme. Always. The app uses a dark color palette.
- COLORS dict in `charts/theme.py` is the single source for all color values.
- Use Dash Bootstrap SLATE theme as the base.
- Custom CSS goes in `assets/custom.css` — never inline styles in Python
  unless it's dynamic (e.g., conditional coloring based on data).

## Commit Message Standards

Follow conventional commits. Every commit message must match:

```
type: short description (imperative mood, lowercase)
```

Valid types:
- `feat` — New feature or page
- `fix` — Bug fix
- `refactor` — Code restructuring (no behavior change)
- `schema` — DDL or migration changes
- `style` — CSS or UI-only changes
- `docs` — Documentation, README, CLAUDE.md updates
- `test` — Test additions or updates
- `deploy` — CI/CD or app.yaml changes
- `chore` — Dependency updates, cleanup

Examples:
- `feat: add risk register page with heatmap`
- `schema: add dependencies table for cross-project tracking`
- `fix: correct velocity chart rolling average calculation`
- `refactor: extract kanban card component from sprint page`

## Branch Strategy

```
main              ← Production (auto-deploys via GitHub Actions)
└── develop       ← Integration branch
    ├── feature/* ← feature/risk-register, feature/portfolio-dashboard
    ├── bugfix/*  ← bugfix/kanban-drag, bugfix/chart-colors
    └── hotfix/*  ← hotfix/auth-fix (branches from main, merges to both)
```

Branch naming: `{type}/{short-kebab-description}`
- Always branch from `develop` (except hotfixes)
- Always PR into `develop` (except hotfixes)
- `develop` → `main` merges are release events

## Git Workflow

This project uses a develop → main branching strategy. Always ensure develop
is synced with main before creating feature branches. After merging PRs, pull
latest into both main and develop. When performing git operations, verify
branch status with `git log --oneline -5` and `git status` before and after
merges.

## Skills & Hooks

After creating, renaming, or modifying any skill file (`.claude/commands/`),
always remind the user to restart their Claude Code session for changes to
take effect. Skills are loaded at session start and won't be recognized
mid-session.

## What NOT To Do

- **Never** put SQL queries in page or service files — SQL lives in repositories only
- **Never** use f-string SQL — always parameterized (`:param_name`)
- **Never** import Dash in services — services are UI-framework-agnostic
- **Never** skip layers (pages must not call repositories directly)
- **Never** build Plotly figures inside page files
- **Never** use Streamlit patterns (st.write, st.columns) — this is Dash
- **Never** commit secrets, tokens, or warehouse IDs
- **Never** modify `schema_ddl.sql` without creating a migration script
- **Never** push directly to `main` — always PR through `develop`
- **Never** use light theme colors — the app is dark theme only

## Key Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-24 | Dash over Streamlit | Full CSS control, native Plotly, Python-maintainable |
| 2026-02-24 | Dash over Flask | Team lacks frontend JS expertise |
| 2026-02-24 | 17-table schema | Supports portfolio → project → phase → sprint → task hierarchy |
| 2026-02-24 | Hybrid waterfall/agile | PMI PMBOK 7 tailoring — governance + execution flexibility |
| 2026-02-24 | Delta time travel over snapshots | Burndown reconstruction without building audit tables |
| 2026-02-24 | sprints.phase_id bridge | Enables hybrid — sprints live inside waterfall phases |
| 2026-02-25 | Layered architecture | Scalable to 13 pages, testable, secure (no SQL injection) |
| 2026-02-25 | Skip Postgres for now | Unity Catalog only — Postgres deferred to future sprint |
| 2026-02-25 | Pydantic BaseSettings | Type-safe config, env var loading, validation |

## Planning Convention

Before starting any non-trivial feature implementation, write the plan to a
file and commit it first. This ensures design work is never lost between
sessions.

```
Write this plan to docs/architecture/PLAN.md, commit it with message
'docs: add architecture plan for [feature]', and push to the current
branch. Do this before starting any implementation.
```

## Quick Reference

### Start local dev
```bash
pip install -r requirements.txt
USE_SAMPLE_DATA=true python app.py
# → http://localhost:8050 (uses sample data fallback)
```

### Deploy to Databricks
```bash
databricks apps deploy pm-hub --source-code-path .
```

### Run tests
```bash
USE_SAMPLE_DATA=true pytest tests/
```

### Run schema
```sql
-- Execute in Databricks notebook or SQL editor
-- File: models/schema_ddl.sql
```

### Create a new page
1. Create `pages/your_page.py` — register route, define `layout()`
2. Add repository functions in `repositories/your_repo.py`
3. Add service functions in `services/your_service.py`
4. Add chart builders in `charts/` (if needed)
5. Extract reusable UI into `components/` (if needed)
6. Add nav link in `app.py` sidebar
