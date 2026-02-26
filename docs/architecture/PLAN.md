# PM Hub — Road to Production Plan

> Last updated: 2026-02-25 | Status: Phase 0 complete, ready for Phase 1

## Context

PM Hub is a Databricks-hosted portfolio and project management app (Dash/Plotly) supporting hybrid waterfall/agile delivery per PMI PMBOK 7. All 13 pages are built with full UI layouts, charts, and sample data. Architecture is clean (Pages→Services→Repos→DB), SQL is parameterized, reviews pass.

**The gap:** The app is currently a read-only dashboard. Only 1 callback exists (breadcrumb). No forms submit, no data refreshes, no cards are clickable. Write operations exist in task_repo but are disconnected from UI. To be a real PM tool, we need:

1. Full CRUD interactivity across all entities
2. Multi-department organizational hierarchy
3. Per-user activity tracking via OBO (who created/changed/deleted what)
4. PMI-aligned risk management (response strategies, triggers, residual risk)
5. Deep portfolio management with business domain hierarchy
6. Change history and real-time edit safety

---

## Phase 0: Schema & Data Model Evolution ✅ COMPLETE

*Structural changes that everything else depends on. Must come first.*
*Completed: 2026-02-25 | PR #19 merged to develop*

### 0.1 — Multi-Department Hierarchy
The app must support multiple departments/business units operating independently.

**New table: `departments`**
```sql
CREATE TABLE departments (
    department_id   STRING NOT NULL,
    name            STRING NOT NULL,
    description     STRING,
    parent_dept_id  STRING,          -- self-ref for hierarchy (e.g., Engineering → Data Engineering)
    head            STRING,          -- department head (user_id)
    created_at      TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_at      TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    is_deleted      BOOLEAN NOT NULL DEFAULT false,
    deleted_at      TIMESTAMP
);
```

**Schema changes:**
- `portfolios` — add `department_id STRING NOT NULL` FK → departments
- `team_members` — add `department_id STRING NOT NULL` FK → departments
- Hierarchy: **Department → Portfolio → Project → Phase/Sprint → Task**
- Data visibility: users see their department's data by default; admins see all

**Files:** `models/schema_ddl.sql`, `models/sample_data.py`, `repositories/department_repo.py` (new), `services/department_service.py` (new)

### 0.2 — Per-User Activity Tracking (created_by / updated_by)
Every write operation must record WHO did it, sourced from OBO headers.

**Schema changes — add to ALL mutable tables:**
- `created_by STRING` — user email from OBO token at creation
- `updated_by STRING` — user email from OBO token at last update
- `deleted_by STRING` — user email who soft-deleted

**Implementation:**
- `auth_service.get_user_email()` already extracts email from `X-Forwarded-Email` header
- All service write functions must accept and pass `user_email` parameter
- All repo INSERT/UPDATE queries include `created_by`/`updated_by` columns
- Audit service logs all mutations with user + timestamp + entity + action

**Files:** `models/schema_ddl.sql` (migration), all `repositories/*.py`, all `services/*.py`

### 0.3 — PMI Risk Management Schema Enhancement
Current risk table is basic. PMI risk management requires deeper tracking.

**Schema changes to `risks` table — add columns:**
- `response_strategy STRING` — avoid | transfer | mitigate | accept | escalate (PMI response types)
- `contingency_plan STRING` — fallback plan if risk materializes
- `trigger_conditions STRING` — early warning signs / risk triggers
- `risk_proximity STRING` — near_term | mid_term | long_term (when might it occur)
- `risk_urgency INT` — 1-5 scale (how soon response is needed)
- `residual_probability INT` — probability after response (1-5)
- `residual_impact INT` — impact after response (1-5)
- `residual_score INT` — residual_probability × residual_impact
- `secondary_risks STRING` — new risks introduced by the response
- `identified_date DATE` — when risk was first identified
- `last_review_date DATE` — when risk was last reviewed
- `response_owner STRING` — who executes the response (may differ from risk owner)

**Risk status lifecycle update:** `identified → qualitative_analysis → response_planning → monitoring → resolved → closed`

**Files:** `models/schema_ddl.sql`, `models/sample_data.py`, `repositories/risk_repo.py`, `pages/risks.py`, `charts/analytics_charts.py`

### 0.4 — Audit Log Table
Centralized audit trail for all entity changes.

**New table: `audit_log`**
```sql
CREATE TABLE audit_log (
    audit_id        STRING NOT NULL,
    user_email      STRING NOT NULL,
    action          STRING NOT NULL,    -- create | update | delete | approve | reject
    entity_type     STRING NOT NULL,    -- task | project | charter | risk | sprint | etc.
    entity_id       STRING NOT NULL,
    field_changed   STRING,             -- which field changed (null for create/delete)
    old_value       STRING,             -- previous value
    new_value       STRING,             -- new value
    details         STRING,             -- JSON blob for complex changes
    created_at      TIMESTAMP NOT NULL DEFAULT current_timestamp()
);
```

**Files:** `models/schema_ddl.sql`, `services/audit_service.py`, `repositories/audit_repo.py` (new)

### 0.5 — Schema Convention Fixes
- Add `created_at` to `project_team` table
- Rename `team_members.joined_at` → `created_at`
- Add `updated_at` to `team_members`

**Files:** `models/schema_ddl.sql`, `models/sample_data.py`

---

## Phase 1: Foundation for Interactivity

*Wire the plumbing that all interactive features depend on.*

### 1.1 — Toast/Alert Feedback System
- Create `components/toast.py` — reusable success/error/warning toast
- Add a toast container to `app.py` main layout
- Pattern: callbacks return toast messages on write success/failure
- **Files:** `components/toast.py` (new), `components/__init__.py`, `app.py`

### 1.2 — Auto-Refresh Callbacks (All 13 Pages)
- Wire `dcc.Interval.n_intervals` → page content refresh on every page
- Pattern: wrap page body in a callback that re-calls the service layer
- Use `dash.callback_context` to distinguish initial load vs refresh
- **Files:** All 13 `pages/*.py`

### 1.3 — Input Validation Layer
- Create `utils/validators.py` — UUID validation, string length limits, enum checks, date range validation
- Services call validators before passing to repos
- **Files:** `utils/validators.py` (new)

### 1.4 — Client-Side State with dcc.Store
- Add `dcc.Store` components for: active department_id, portfolio_id, project_id, sprint_id, user context
- Pages read from Store rather than hardcoding IDs
- Enables drill-down navigation (click department → portfolio → project)
- **Files:** `app.py`, pages that need context

### 1.5 — Error Boundary Implementation
- Make `components/error_boundary.py` actually catch callback exceptions
- Show user-friendly error message instead of blank screen
- **Files:** `components/error_boundary.py`

### 1.6 — Change History Pattern
- Leverage Delta Lake time travel for point-in-time reconstruction (burndown already uses this)
- For user-facing history: audit_log table (Phase 0.4) records field-level changes
- `safe_update()` already does optimistic locking via `updated_at` — enforce it on ALL writes
- Add "Last modified by [user] at [time]" footer to all edit modals
- **Files:** `repositories/base.py` (ensure safe_update used everywhere), `services/audit_service.py`

---

## Phase 2: Core CRUD Operations

*The daily-use features that make this a PM tool, not a report viewer.*

### 2.1 — Task CRUD + Kanban Interactivity
- **Create task modal:** title, type (epic/story/task/bug), priority, story points, assignee, description
- **Kanban status updates:** Click-to-move between columns (todo→in_progress→review→done) via dropdown per card
- **Edit task modal:** Click task card → edit fields → save
- **Delete task:** Soft delete with confirmation dialog
- All writes record `created_by` / `updated_by` from OBO
- Wire to existing `task_service.create_task()`, `update_task_status()`, `move_task_to_sprint()`
- Add `task_service.update_task()`, `task_service.delete_task()`
- Add `task_repo.update_task()`, `task_repo.delete_task()` (using `safe_update`, `soft_delete`)
- **Files:** `pages/sprint.py`, `pages/my_work.py`, `pages/backlog.py`, `services/task_service.py`, `repositories/task_repo.py`

### 2.2 — Charter Form Submission + Approval Workflow
- Wire the existing 11-field charter form to a submit callback
- Charter versioning (version increments on update, old version preserved via Delta time travel)
- Charter approval workflow: `draft → submitted → under_review → approved → rejected`
- Approval action records `approved_by` + `approved_date` from OBO user
- Add `charter_service.py` (new), `charter_repo.py` write operations
- **Files:** `pages/charters.py`, `services/charter_service.py` (new), `repositories/charter_repo.py`

### 2.3 — Sprint Management
- Create sprint modal (name, goal, start/end dates, capacity, phase assignment for hybrid)
- Close sprint action (marks closed, captures velocity, optionally creates next sprint)
- Sprint selector dropdown on sprint page
- Move tasks between sprints
- Add `sprint_service.create_sprint()`, `sprint_service.close_sprint()`
- Add `sprint_repo.create_sprint()`, `sprint_repo.close_sprint()`
- **Files:** `pages/sprint.py`, `services/sprint_service.py`, `repositories/sprint_repo.py`

### 2.4 — PMI Risk Management (Full Lifecycle)
- **Create risk modal:** title, category, probability (1-5), impact (1-5), description, owner, response strategy (avoid/transfer/mitigate/accept/escalate), mitigation plan, contingency plan, triggers, urgency, proximity, response owner
- **Risk scoring:** auto-calculate risk_score (P×I), residual_score after response
- **Risk status lifecycle:** identified → qualitative_analysis → response_planning → monitoring → resolved → closed
- **Risk review:** track last_review_date, flag risks overdue for review
- **Residual risk tracking:** after response, what's the remaining risk?
- **Secondary risk identification:** does the response introduce new risks?
- **Enhanced heatmap:** toggle between inherent risk (before response) and residual risk (after response)
- **Risk burndown:** chart showing open risk score over time
- Add `risk_service.py` (new), expand `risk_repo.py` with CRUD
- **Files:** `pages/risks.py`, `services/risk_service.py` (new), `repositories/risk_repo.py`, `charts/analytics_charts.py`, `models/sample_data.py`

### 2.5 — Retrospective CRUD + Voting
- Add retro item (went_well / improve / action) via inline form
- Vote on items (increment vote count, one vote per user)
- Mark action items as done / convert to task
- Sprint selector for retros
- Add `retro_service.py` (new), `retro_repo.py` (new)
- **Files:** `pages/retros.py`, `services/retro_service.py` (new), `repositories/retro_repo.py` (new), `models/sample_data.py`

### 2.6 — Project & Portfolio CRUD
- Create/edit project form (name, portfolio, department, delivery method, budget, dates, owner, sponsor)
- Create/edit portfolio form (name, department, description, owner, strategic priority)
- Soft delete with cascading considerations
- **Files:** `pages/projects.py`, `pages/portfolios.py`, `services/project_service.py`, `services/portfolio_service.py`, `repositories/project_repo.py`, `repositories/portfolio_repo.py`

---

## Phase 3: Navigation, Hierarchy & Multi-Department

*Connect the pages so users flow naturally through the organizational hierarchy.*

### 3.1 — Department → Portfolio → Project Drill-Down
- Dashboard shows department-level rollup (or all departments for admins)
- Click department → portfolios page filtered by department
- Click portfolio card → projects page filtered by portfolio
- Click project card → project detail view (gantt, charters, sprint, risks)
- URL state: `/portfolios?department_id=xxx`, `/projects?portfolio_id=xxx`
- **Files:** `pages/dashboard.py`, `pages/portfolios.py`, `pages/projects.py`, `app.py`

### 3.2 — Department Selector in Nav
- Add department dropdown to topbar (for users with access to multiple departments)
- Sets department context via dcc.Store → filters all downstream pages
- Admin users see "All Departments" option
- **Files:** `app.py`, `services/department_service.py`, `services/auth_service.py`

### 3.3 — Project Context Selector
- Persistent project selector (dropdown) that sets context across sprint, gantt, charters, risks pages
- When user selects project → all sub-pages show that project's data
- Store selected project_id in `dcc.Store`
- **Files:** `app.py`, project-level pages (sprint, gantt, charters, risks, retros, reports)

### 3.4 — Filtering and Sorting
- Add filter controls to data-heavy pages: status, assignee, priority, date range, department
- Sort toggles on tables (risk register, resource table, backlog)
- **Files:** `pages/backlog.py`, `pages/risks.py`, `pages/resources.py`, `pages/projects.py`

---

## Phase 4: PMI/PMP Feature Completeness

*Fill out remaining PMBOK 7 knowledge areas.*

### 4.1 — Phase & Gate Management (Waterfall Governance)
- Create/edit phases with delivery method (waterfall/agile/hybrid)
- Gate approval workflow: pending → approved → rejected → deferred (with approver + date from OBO)
- Phase status auto-calculation from task/deliverable completion %
- Gate criteria checklist
- Add `phase_service.py` (new), write ops in `project_repo.py`
- **Files:** `pages/gantt.py`, `services/phase_service.py` (new), `repositories/project_repo.py`

### 4.2 — Deliverables Tracking
- Create deliverables linked to phases (name, description, owner, due date, artifact URL)
- Status: not_started → in_progress → submitted → approved
- Deliverables table exists in schema but has no repo/service/UI
- Add sample data
- **Files:** `pages/gantt.py` (deliverables section), `repositories/deliverable_repo.py` (new), `services/deliverable_service.py` (new), `models/sample_data.py`

### 4.3 — Dependencies View
- Task-to-task and project-to-project dependency mapping
- Blocked/blocking indicators on task cards and roadmap
- Dependency types: blocking, dependent, shared_resource, informational
- Dependencies table exists in schema but unused
- **Files:** `pages/roadmap.py`, `repositories/dependency_repo.py` (new), `services/dependency_service.py` (new), `models/sample_data.py`

### 4.4 — Comments & Collaboration
- Task comment threads (add/view per task, inside task detail modal)
- Comments recorded with author from OBO
- Comments table exists in schema but unused
- **Files:** Task detail modal in `pages/sprint.py`, `repositories/comment_repo.py` (new), `services/comment_service.py` (new), `models/sample_data.py`

### 4.5 — Time Tracking
- Log hours per task (time_entries table exists in schema)
- Show time spent vs estimated on task cards
- Resource utilization chart updated with actual hours
- **Files:** `pages/resources.py`, `repositories/time_entry_repo.py` (new), `services/time_entry_service.py` (new), `models/sample_data.py`

### 4.6 — Resource Management Enhancements
- Team member assignment to projects (project_team CRUD)
- Allocation % management (over-allocation warnings)
- Capacity planning view (who's available, who's overloaded)
- Department-filtered resource views
- **Files:** `pages/resources.py`, `repositories/resource_repo.py`, `services/resource_service.py` (new)

---

## Phase 5: Polish & Production Readiness

### 5.1 — Export to Excel
- Implement `export_service.to_excel()` using openpyxl
- Wire export_button to pages: risks, backlog, resources, reports, projects
- Add `openpyxl` to requirements.txt
- **Files:** `services/export_service.py`, relevant pages, `requirements.txt`

### 5.2 — Auth & RBAC Enforcement
- Implement `has_permission()` with role-based checks:
  - `admin` — all departments, all operations
  - `lead` / `pm` — own department, full CRUD
  - `engineer` — own projects, task CRUD only
  - `viewer` — read-only across assigned projects
- Gate write operations behind role checks in services
- Show/hide UI elements (create buttons, edit actions) based on permissions
- Department-scoped data visibility (users only see their department's data)
- **Files:** `services/auth_service.py`, all services with writes, all pages with edit actions

### 5.3 — Specific Exception Handling
- Replace broad `except Exception` in `unity_catalog.py` with Databricks-specific exceptions
- Switch to `fetchall_arrow().to_pandas()` for efficiency
- **Files:** `db/unity_catalog.py`

### 5.4 — Test Coverage
- Service layer unit tests (business logic, validation, edge cases)
- Repository tests against sample data
- Callback tests (simulate inputs, verify outputs)
- Use `ast.parse` for syntax validation (no local Dash runtime)
- **Files:** `tests/test_services/`, `tests/test_repositories/`, `tests/test_callbacks/`

### 5.5 — Notification System
- Persist notifications to DB
- Show unread count badge in topbar
- Notification dropdown panel
- Trigger on: task assignment, charter approval, gate decisions, risk escalation, sprint close
- **Files:** `services/notification_service.py`, `repositories/notification_repo.py` (new), `app.py`, `models/schema_ddl.sql`

---

## Anticipated Problems & Mitigations

| Problem | Mitigation |
|---------|------------|
| **Callback ID collisions** across 13+ pages | Page-specific prefixes for all component IDs (e.g., `sprint-task-modal`, `risk-create-btn`) |
| **Concurrent edits** (two users update same task) | `safe_update()` with optimistic locking via `updated_at` — enforce on ALL writes |
| **Real-time edit visibility** | Delta CDC + audit_log table for change tracking; auto-refresh at 30s interval shows latest |
| **Department data isolation** | All queries filter by `department_id` from user context; admin override for cross-dept views |
| **Who changed what?** | `created_by`/`updated_by` on all tables + `audit_log` for field-level change history |
| **Local dev can't test writes** | Add in-memory write mode that mutates sample DataFrames for local testing |
| **Component ID explosion** | Dash pattern-matching callbacks (`MATCH`, `ALL`) for repeated elements |
| **Form validation UX** | Client-side validation (required fields) + server-side (business rules) → specific field errors via toast |
| **Large data volumes** | Paginate tables, lazy-load charts, limit default date ranges |
| **Stale data after writes** | Auto-refresh re-fetches after mutation; callback chaining for immediate UI update |
| **Risk schema migration** | Add new columns with defaults; existing rows get null for new fields — no data loss |
| **Department migration** | Create default "General" department; assign all existing portfolios/users to it |

---

## Execution Order

Work in phase order. Within each phase, tasks can be parallelized.

- **Phase 0** (Schema) → structural changes everything depends on
- **Phase 1** (Foundation) → plumbing for interactivity
- **Phase 2** (Core CRUD) → the bulk of the work, highest user value
- **Phase 3** (Navigation & Multi-Dept) → organizational hierarchy
- **Phase 4** (PMI Features) → PMBOK 7 knowledge area coverage
- **Phase 5** (Polish) → production hardening

Each phase ends with a `/review-all` cycle.

---

## Verification

After each phase:
1. `python -c "import ast; ast.parse(open('file.py').read())"` on all modified files
2. Run smoke tests: `pytest tests/test_pages/test_smoke.py`
3. Run `/review-all` to check architecture, security, Databricks compliance
4. Manual verification with sample data (pages render, callbacks fire, writes succeed)
