# PM Hub — Road to Production Plan

> Last updated: 2026-02-26 | Status: Phase 2 COMPLETE (all CRUD done), Phase 3 next

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

## Phase 1: Foundation for Interactivity ✅ COMPLETE

*Wire the plumbing that all interactive features depend on.*
*Completed: 2026-02-25 | PR #20 merged to develop | 24 files changed, +1,524 lines*

### 1.1 — Toast/Alert Feedback System ✅
- Created `components/toast.py` — `toast_container()` with `dbc.Toast` (auto-dismiss 4s, positioned top-right)
- Created `callbacks/toast_callbacks.py` — listens on `toast-store` for success/error/warning/info messages
- `make_toast_output()` helper for callbacks that want direct toast control
- Pages trigger toasts via: `Output("toast-store", "data")` → `{"message": "...", "type": "success", "header": "..."}`
- **Files:** `components/toast.py` (new), `callbacks/toast_callbacks.py` (new), `components/__init__.py`, `app.py`

### 1.2 — Auto-Refresh Callbacks (All 13 Pages) ✅
- All 13 pages refactored: `layout()` → thin wrapper, `_build_content()` → full content builder
- Each page has unique `dcc.Interval` ID (e.g., `dashboard-refresh-interval`) — no duplicate IDs
- Callbacks wire interval Input to content container Output for 30-second auto-refresh
- `charters.py` gained auto-refresh (previously missing)
- **Files:** All 13 `pages/*.py`

### 1.3 — Input Validation Layer ✅
- Created `utils/validators.py` — 11 individual validators, 5 composite validators
- `ValidationError` and `ValidationResult` classes for batch error collection
- 20+ domain enum constants aligned with `schema_ddl.sql` (TASK_STATUSES, RISK_STATUSES, etc.)
- Composite validators: `validate_task_create`, `validate_risk_create`, `validate_sprint_create`, `validate_project_create`, `validate_retro_item_create`
- **Files:** `utils/validators.py` (new)

### 1.4 — Client-Side State with dcc.Store ✅
- Created `components/app_state.py` — `app_stores()` returns 6 `dcc.Store` components
- Stores: `active-department-store`, `active-portfolio-store`, `active-project-store`, `active-sprint-store`, `user-context-store` (session), `toast-store` (memory)
- Created `callbacks/state_callbacks.py` — URL-driven state updates (`?department_id=`, `?portfolio_id=`, etc.) and user context initialization
- **Files:** `components/app_state.py` (new), `callbacks/state_callbacks.py` (new), `app.py`

### 1.5 — Error Boundary Implementation ✅
- Rewrote `components/error_boundary.py` with proper Dash error handling
- `safe_render(fn)` — catches exceptions during layout building, shows error card
- `safe_callback(msg)` — decorator for callbacks, catches and logs exceptions, returns error UI
- `_error_card()` — dismissable `dbc.Alert` with expandable technical details
- Original `error_boundary()` kept as passthrough for backwards compatibility
- **Files:** `components/error_boundary.py`

### 1.6 — Change History Pattern ✅
- Created `services/change_history_service.py` — `track_update()` (field-level diff), `track_create()`, `track_delete()`, `track_approval()`, `get_history()`
- Field-level change detection: compares old vs new dicts, logs each changed field to `audit_log` via `audit_service`
- Created `components/change_history.py` — `change_history_panel()` timeline UI, `last_modified_footer()` for edit modals
- **Files:** `services/change_history_service.py` (new), `components/change_history.py` (new), `components/__init__.py`

---

## Phase 2: Core CRUD Operations

*The daily-use features that make this a PM tool, not a report viewer.*
*Split into 2a (highest daily-use value) and 2b (remaining entities) for manageable delivery.*

### Prerequisites ✅ COMPLETE

*Completed: 2026-02-26 | PR #22 merged to develop*

#### 2.0a — In-Memory Write Mode for Local Dev ✅
- Extended `models/sample_data.py` with mutable module-level store (`_store` dict)
- Added `create_record()`, `update_record()`, `delete_record()` helpers with audit column defaults
- Wired `repositories/base.py` — `write()` routes to in-memory store when `USE_SAMPLE_DATA=true`
- `safe_update()` supports both optimistic locking (with `expected_updated_at`) and non-locking updates (when `None`)
- **Files:** `models/sample_data.py`, `repositories/base.py`

#### 2.0b — Shared CRUD Modal Component ✅
- Created `components/crud_modal.py` — 6 public functions: `crud_modal()`, `confirm_delete_modal()`, `get_modal_values()`, `set_field_errors()`, `modal_field_states()`, `modal_error_outputs()`
- ID convention: all component IDs prefixed with `id_prefix` to avoid collisions
- Created `components/task_fields.py` — shared `TASK_FIELDS`, `SPRINT_FIELDS`, `TEAM_MEMBER_OPTIONS`
- **Files:** `components/crud_modal.py` (new), `components/task_fields.py` (new), `components/__init__.py`

### Phase 2a — Task & Sprint CRUD ✅ COMPLETE

*Completed: 2026-02-26 | PR #23 merged to develop*

#### 2.1 — Task CRUD + Kanban Interactivity ✅
- **Sprint page** (`pages/sprint.py`): Full overhaul with task create/edit/delete modals, kanban status dropdowns, sprint selector, toolbar
- **Backlog page** (`pages/backlog.py`): Create task, edit task, delete task, move-to-sprint dropdown per row
- **My Work page** (`pages/my_work.py`): Edit task modal, inline status change dropdowns
- Pattern-matching callbacks for per-card/per-row actions (`{"type": "sprint-task-status-dd", "index": task_id}`)
- Mutation-triggered refresh: `dcc.Store` counter bridges CRUD callbacks and auto-refresh (avoids Dash single-Output constraint)
- Toast feedback on all create/update/delete operations
- Validation via `utils/validators.py` → service layer → specific field errors
- **Repos:** `get_task_by_id()`, `update_task()`, `delete_task()` added to `task_repo.py` (using `safe_update`, `soft_delete`)
- **Services:** `create_task_from_form()`, `update_task_from_form()`, `delete_task()`, `get_task()` with result dict pattern `{"success": bool, "errors": dict, "message": str}`
- **Files:** `pages/sprint.py`, `pages/backlog.py`, `pages/my_work.py`, `services/task_service.py`, `repositories/task_repo.py`

#### 2.2 — Sprint Management ✅
- Sprint selector dropdown on sprint page (all sprints, active selected by default)
- Create sprint modal (name, goal, start/end dates, capacity) with validation
- Close sprint action (marks status → closed)
- **Repos:** `create_sprint()`, `close_sprint()`, `get_sprint_by_id()`, `update_sprint()` in `sprint_repo.py`
- **Services:** `create_sprint_from_form()`, `close_sprint()`, `get_sprint()` with result dict pattern
- **Sample data:** Tasks now have `project_id`, `sprint_id`, `assignee` columns; sprints have `project_id`, `goal`; 2 backlog tasks added
- **Files:** `pages/sprint.py`, `services/sprint_service.py`, `repositories/sprint_repo.py`, `models/sample_data.py`

### Phase 2b — Charter, Risk, Retro & Portfolio CRUD

#### 2.3 — Charter Form Submission + Approval Workflow ✅

*Completed: 2026-02-26 | PR #24 to develop*

- Full charter CRUD: create, edit, delete via crud_modal (12 fields, size xl)
- Charter approval workflow: `draft → submitted → under_review → approved → rejected`
- Status-guarded transitions: submit (draft/rejected only), approve/reject (submitted/under_review only)
- Approval records `approved_by` + `approved_date` from OBO user with optimistic locking
- `validate_charter_create()` composite validator added to `utils/validators.py`
- **Services:** `charter_service.py` (new) — `create_charter_from_form()`, `update_charter_from_form()`, `submit_charter()`, `approve_charter()`, `reject_charter()`, `delete_charter()` with result dict pattern
- **Repos:** `charter_repo.py` — expanded with `get_charters()`, `get_charter_by_id()`, `create_charter()`, `update_charter()`, `delete_charter()`, `update_charter_status()`
- **Pages:** `pages/charters.py` — complete rewrite with 8 callbacks (refresh, toggle modal, save, submit, approve, reject, delete flow, cancel)
- **Sample data:** Charter seed now includes `status`, `version`, `description`, `created_by`, `updated_by` fields
- **Files:** `pages/charters.py`, `services/charter_service.py` (new), `repositories/charter_repo.py`, `utils/validators.py`, `models/sample_data.py`

#### 2.4 — PMI Risk Management (Full Lifecycle) ✅

*Completed: 2026-02-26 | PR #24 to develop*

- Full risk CRUD: create, edit, delete via crud_modal (12 PMI fields, size xl)
- **Risk scoring:** auto-calculate `risk_score = P × I` on create and update
- **Risk status lifecycle:** `identified → qualitative_analysis → response_planning → monitoring → resolved → closed` with validated enum transitions
- **Risk review:** "Mark as reviewed" button updates `last_review_date`, overdue review KPI (>14 days)
- **Residual risk tracking:** residual_probability, residual_impact, residual_score displayed in table
- **Enhanced heatmap:** toggle between inherent risk (probability/impact) and residual risk (residual_probability/residual_impact)
- **5 KPI cards:** Total Risks, High Severity, Avg Score, Open/Active, Overdue Review
- Inline status dropdown per risk row (pattern-matching callbacks)
- Defense-in-depth: status validation in both page callback and service layer
- **Services:** `risk_service.py` (new) — `create_risk_from_form()`, `update_risk_from_form()`, `delete_risk()`, `update_risk_status()`, `review_risk()` with result dict pattern
- **Repos:** `risk_repo.py` — expanded with `create_risk()`, `update_risk()`, `delete_risk()`, `update_risk_status()` (26-column allowlist)
- **Charts:** `analytics_charts.py` — added `risk_heatmap_residual()` for residual risk view
- **Analytics service:** added `get_risks_by_project()`, `get_risks_overdue_review()` passthroughs
- **Files:** `pages/risks.py`, `services/risk_service.py` (new), `repositories/risk_repo.py`, `charts/analytics_charts.py`, `services/analytics_service.py`

#### 2.5 — Retrospective CRUD + Voting ✅

*Completed: 2026-02-26 | PR #26 to develop*

- Full retro item CRUD: create, edit, delete via crud_modal (category + body fields)
- Sprint selector dropdown (all sprints, defaults to most recent closed)
- Vote on items (atomic increment, works in both sample data and production)
- Convert action items to tasks (marks status as "converted")
- Three-column retro board (went_well, improve, action_item) with per-card action buttons
- 4 KPI cards: Total Items, Total Votes, Action Items, Converted
- Pattern-matching callbacks for vote/edit/delete/convert per card
- **Services:** `retro_service.py` (new) — `create_retro_item_from_form()`, `update_retro_item_from_form()`, `delete_retro_item()`, `vote_retro_item()`, `convert_to_task()` with result dict pattern
- **Repos:** `retro_repo.py` (new) — `get_retro_items()`, `get_retro_item_by_id()`, `create_retro_item()`, `update_retro_item()`, `delete_retro_item()`, `vote_retro_item()`, `convert_to_task()`
- **Analytics:** `analytics_service.py` now routes retro items through `retro_repo` instead of `resource_repo`
- **Sample data:** Retro items now include `author`, `status`, `item_text` alias columns
- **Files:** `pages/retros.py`, `services/retro_service.py` (new), `repositories/retro_repo.py` (new), `services/analytics_service.py`, `models/sample_data.py`

#### 2.6 — Project & Portfolio CRUD ✅

*Completed: 2026-02-26 | PR #26 to develop*

- Full project CRUD: create, edit, delete via crud_modal (9 fields: name, delivery_method, status, health, owner, start_date, target_date, budget, description)
- Full portfolio CRUD: create, edit, delete via crud_modal (4 fields: name, owner, description, strategic_priority)
- `validate_portfolio_create()` composite validator added to `utils/validators.py`
- Project cards with edit/delete buttons, health badges, progress bars
- Portfolio sections with edit/delete buttons, KPI strip, charts preserved
- **Services:** `project_service.py` expanded — `create_project_from_form()`, `update_project_from_form()`, `delete_project()`, `get_projects()`
- **Services:** `portfolio_service.py` expanded — `create_portfolio_from_form()`, `update_portfolio_from_form()`, `delete_portfolio()`, `get_portfolio()`
- **Repos:** `project_repo.py` expanded — `get_projects()`, `get_project_by_id()`, `create_project()`, `update_project()`, `delete_project()` (17-column allowlist)
- **Repos:** `portfolio_repo.py` expanded — `get_portfolio_by_id()`, `create_portfolio()`, `update_portfolio()`, `delete_portfolio()` (9-column allowlist)
- **Sample data:** Portfolios now include `description`, `strategic_priority`, `created_by`; projects include `owner`, `sponsor`, `department_id`, `created_by`
- **Files:** `pages/projects.py`, `pages/portfolios.py`, `services/project_service.py`, `services/portfolio_service.py`, `repositories/project_repo.py`, `repositories/portfolio_repo.py`, `utils/validators.py`, `models/sample_data.py`

---

## Phase 3: Navigation, Hierarchy & Multi-Department

*Connect the pages so users flow naturally through the organizational hierarchy.*
*Note: 3.1 and 3.2 (drill-down navigation, department selector) have no dependency on Phase 2 CRUD and can be developed in parallel with Phase 2b if desired.*

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
| **Local dev can't test writes** | In-memory write mode (task 2.0a) — mutates sample DataFrames when `USE_SAMPLE_DATA=true` |
| **Component ID explosion** | Dash pattern-matching callbacks (`MATCH`, `ALL`) for repeated elements |
| **Form validation UX** | Client-side validation (required fields) + server-side (business rules) → specific field errors via toast |
| **Large data volumes** | Paginate tables, lazy-load charts, limit default date ranges |
| **Stale data after writes** | Auto-refresh re-fetches after mutation; callback chaining for immediate UI update |
| **Risk schema migration** | Add new columns with defaults; existing rows get null for new fields — no data loss |
| **Department migration** | Create default "General" department; assign all existing portfolios/users to it |

---

## Execution Order

Work in phase order. Within each phase, tasks can be parallelized.

- **Phase 0** (Schema) ✅ → structural changes everything depends on
- **Phase 1** (Foundation) ✅ → plumbing for interactivity
- **Phase 2 prereqs** (In-memory writes + shared modal) ✅ → unblocked all CRUD work
- **Phase 2a** (Task & Sprint CRUD) ✅ → highest daily-use value, completed
- **Phase 2b** (Charter + Risk + Retro + Project/Portfolio CRUD) ✅ → ALL COMPLETE
- **Phase 3** (Navigation & Multi-Dept) → organizational hierarchy — NEXT
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

### Phase 2+ Test Requirements
Starting with Phase 2, CRUD operations need deeper testing beyond `ast.parse`:
- **Callback integration tests:** Simulate modal open/close, form submission, toast feedback using `dash.testing` or by mocking callback context
- **Service layer tests:** Validate business logic (e.g., risk score calculation, charter version increment, sprint velocity capture)
- **In-memory write tests:** Verify that create/update/delete operations against sample data produce correct state
- **Validation round-trip tests:** Submit invalid data → verify field-level errors returned → fix → verify success
- Test pattern: `tests/test_callbacks/test_{page}_crud.py` for each CRUD page
