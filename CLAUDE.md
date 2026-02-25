# CLAUDE.md — PM Hub Project Intelligence

> Claude reads this file automatically at the start of every session.
> Last updated: 2026-02-24 | Current Phase: 1 (Planning & Design)

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

See [docs/architecture-plan.md](docs/architecture-plan.md) for the full scaffolding & architecture plan.
**Current step**: Not started — plan approved, ready for Step 1 (Local Postgres setup)
**Pattern**: Pragmatic Layered Architecture with Repository Pattern
**Call direction**: Pages → Services → Repositories → DB (never skip layers)

## Current State

<!-- UPDATE THIS SECTION AS THE PROJECT PROGRESSES -->
- **Phase**: 1 — Planning & Design (Waterfall)
- **Sprint**: N/A (sprints begin in Phase 3)
- **Focus**: Architecture scaffolding — implementing the layered architecture plan
- **Blockers**: None
- **Next Gate**: Gate 1 — Charter & Architecture Approved

## Architecture Rules

### File Structure — Follow Exactly
```
databricks-pm-app/
├── app.py                  # Main entry point — DO NOT put page logic here
├── app.yaml                # Databricks Apps config — warehouse ID goes here
├── requirements.txt        # Pin versions. Always.
├── models/
│   ├── schema_ddl.sql      # Single source of truth for all table definitions
│   └── migrations/         # Incremental schema changes (numbered: 001_, 002_)
├── pages/                  # One file per route. Dash multi-page app pattern.
│   ├── dashboard.py        # /
│   ├── charters.py         # /charters
│   └── sprint.py           # /sprint (etc.)
├── utils/
│   ├── data_access.py      # ALL database queries go here. No SQL in pages.
│   └── charts.py           # ALL Plotly figure builders go here.
├── static/css/             # Custom CSS overrides
├── assets/                 # Dash auto-loads from here (custom.css)
└── tests/                  # Validation queries and smoke tests
```

### Patterns — Always Follow These

**Pages** — Every page file must:
1. Import `dash` and register with `dash.register_page(__name__, path="/route")`
2. Define a `layout()` function (not a variable)
3. Import data from `utils/data_access.py` — never write SQL inline
4. Import chart builders from `utils/charts.py` — never build figures inline
5. Use Dash Bootstrap Components for layout (dbc.Row, dbc.Col, dbc.Card)

**Data Access** — `utils/data_access.py` rules:
1. Every query is a named function: `get_portfolios()`, `get_sprint_tasks(sprint_id)`
2. Functions return `pd.DataFrame` always
3. Parameterized queries use f-strings with the parameter (we're inside Unity Catalog auth)
4. Every function has a sample data fallback for local development
5. Write operations (INSERT, UPDATE) are separate functions with explicit names

**Charts** — `utils/charts.py` rules:
1. Every chart is a function that takes a DataFrame and returns a `go.Figure`
2. All figures call `apply_theme(fig)` before returning
3. Color constants live in the `COLORS` dict at the top of the file
4. Never hardcode colors inside chart functions

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
- COLORS dict in `charts.py` is the single source for all color values.
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

## What NOT To Do

- **Never** put SQL queries directly in page files
- **Never** build Plotly figures inside page files
- **Never** use Streamlit patterns (st.write, st.columns) — this is Dash
- **Never** use `WidthType.PERCENTAGE` in docx generation — always DXA
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

## Quick Reference

### Start local dev
```bash
pip install -r requirements.txt
python app.py
# → http://localhost:8050 (uses sample data fallback)
```

### Deploy to Databricks
```bash
databricks apps deploy pm-hub --source-code-path .
```

### Run schema
```sql
-- Execute in Databricks notebook or SQL editor
-- File: models/schema_ddl.sql
```

### Create a new page
1. Create `pages/your_page.py`
2. Add query functions to `utils/data_access.py`
3. Add chart builders to `utils/charts.py` (if needed)
4. Add nav link in `app.py` sidebar
