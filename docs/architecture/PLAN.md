# PM Hub — Road to Production Plan

> Last updated: 2026-02-27 | Status: Phase 5 COMPLETE + Post-Production Improvements

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

## Phase 3: Navigation, Hierarchy & Multi-Department ✅ COMPLETE

*Connect the pages so users flow naturally through the organizational hierarchy.*
*Completed: 2026-02-26 | PR #27 to develop*

### 3.1 — Department → Portfolio → Project Drill-Down ✅

*Completed: 2026-02-26*

- Dashboard shows department cards with drill-down links to `/portfolios?department_id=xxx`
- Department cards display name, portfolio count, member count
- Portfolio cards wrapped in `dcc.Link` for drill-down to `/projects?portfolio_id=xxx`
- Portfolios page filters by `department_id` from URL params or active-department-store
- Projects page filters by `portfolio_id` from URL params
- Context-aware breadcrumbs with `dcc.Link` for clickable navigation segments
- **New components:** `components/department_selector.py`, `components/project_selector.py`
- **New callbacks:** `callbacks/department_callbacks.py`, `callbacks/project_callbacks.py`
- **Modified:** `pages/dashboard.py`, `pages/portfolios.py`, `pages/projects.py`, `components/portfolio_card.py`, `callbacks/navigation.py`
- **Repo/Service:** `repositories/portfolio_repo.py` (department_id filter), `services/portfolio_service.py` (department_id passthrough)

### 3.2 — Department Selector in Nav ✅

*Completed: 2026-02-26*

- Department dropdown added to topbar (`topbar-dept-selector`)
- Options populated via callback from `department_service.get_departments()`
- Selection updates `active-department-store` → filters downstream pages
- Clearable (shows "All Departments" when cleared)
- **Files:** `components/department_selector.py` (new), `callbacks/department_callbacks.py` (new), `app.py`

### 3.3 — Project Context Selector ✅

*Completed: 2026-02-26*

- Project dropdown added to topbar (`topbar-project-selector`)
- Options filtered by active department when set
- Selection updates `active-project-store` → all sub-pages show that project's data
- 7 pages now use `active-project-store`: sprint, gantt, charters, backlog, retros, reports, risks
- Replaced hardcoded `"prj-001"` with `active_project or "prj-001"` fallback
- **Files:** `components/project_selector.py` (new), `callbacks/project_callbacks.py` (new), `app.py`, `pages/sprint.py`, `pages/gantt.py`, `pages/charters.py`, `pages/backlog.py`, `pages/retros.py`, `pages/reports.py`

### 3.4 — Filtering and Sorting ✅

*Completed: 2026-02-26*

- Created reusable `components/filter_bar.py` with `filter_bar()` and `sort_toggle()` functions
- Supports "select" (multi-dropdown), "text" (debounced input), "date_range" (DatePickerRange)
- Component IDs follow `{page_prefix}-{filter_id}-filter` pattern
- **Projects page:** status, health, delivery method filters + sort by name/health/completion
- **Backlog page:** status, priority, assignee, type filters
- **Risks page:** status, category filters + owner text search + sort by risk_score/created_at/last_review_date
- **Resources page:** role filter
- All filtering done Python-side on DataFrame after fetch
- **Files:** `components/filter_bar.py` (new), `pages/projects.py`, `pages/backlog.py`, `pages/risks.py`, `pages/resources.py`

---

## Phase 4: PMI/PMP Feature Completeness ✅ COMPLETE

*Fill out remaining PMBOK 7 knowledge areas.*
*Completed: 2026-02-26 | PR #29 to develop*

### 4.1 — Phase & Gate Management (Waterfall Governance) ✅

*Completed: 2026-02-26*

- Full phase CRUD: create/edit/delete via crud_modal (name, phase_type, delivery_method, start/end dates)
- Gate approval workflow: pending → approved → rejected → deferred (with approver + date + decision notes from OBO)
- Gate criteria management: criteria text field, decision comments
- Enhanced sample data: phases now include `project_id`, `created_by`; gates include `name`, `criteria`, `decision`
- **New services:** `services/phase_service.py` — `create_phase_from_form()`, `update_phase_from_form()`, `delete_phase()`, `approve_gate()`, `reject_gate()`, `defer_gate()`
- **New repos:** `repositories/phase_repo.py`, `repositories/gate_repo.py` — full CRUD with parameterized queries
- **New validators:** `validate_phase_create()`, `validate_gate_create()` in `utils/validators.py`
- **Pages:** `pages/gantt.py` — complete rewrite with 12 callbacks (phase CRUD, gate approval workflow, refresh)
- **Files:** `pages/gantt.py`, `services/phase_service.py` (new), `repositories/phase_repo.py` (new), `repositories/gate_repo.py` (new), `utils/validators.py`, `models/sample_data.py`

### 4.2 — Deliverables Tracking ✅

*Completed: 2026-02-26*

- **New page:** `pages/deliverables.py` at `/deliverables` with full CRUD
- Create deliverables linked to phases (name, description, owner, due date, artifact URL, status)
- Status lifecycle: not_started → in_progress → submitted → complete → approved
- Phase filter dropdown, status filter, sort by due_date/status/name
- 3 KPI cards: Total Deliverables, Complete, Overdue
- **New services:** `services/deliverable_service.py` — `create_deliverable_from_form()`, `update_deliverable_from_form()`, `delete_deliverable()`
- **New repos:** `repositories/deliverable_repo.py` — full CRUD with phase JOIN
- **New validators:** `validate_deliverable_create()` in `utils/validators.py`
- **Sample data:** 5 deliverables across phases with realistic artifacts
- **Files:** `pages/deliverables.py` (new), `services/deliverable_service.py` (new), `repositories/deliverable_repo.py` (new), `utils/validators.py`, `models/sample_data.py`

### 4.3 — Dependencies View ✅

*Completed: 2026-02-26*

- **Roadmap page** (`pages/roadmap.py`): complete rewrite with dependency CRUD
- Cross-project dependency mapping (source/target projects + optional tasks)
- Dependency types: blocking, dependent, shared_resource, informational
- Risk levels: low, medium, high, critical
- Status lifecycle: active → accepted → mitigated → resolved
- Filter by type, risk_level, status + sort toggles
- 4 KPI cards: Total Dependencies, Blocking, High Risk, Resolved
- **New services:** `services/dependency_service.py` — `create_dependency_from_form()`, `update_dependency_from_form()`, `delete_dependency()` with cross-validation (source ≠ target)
- **New repos:** `repositories/dependency_repo.py` — full CRUD with source/target project filtering
- **New validators:** `validate_dependency_create()` in `utils/validators.py`
- **Sample data:** 4 dependencies across projects with realistic descriptions
- **Files:** `pages/roadmap.py`, `services/dependency_service.py` (new), `repositories/dependency_repo.py` (new), `utils/validators.py`, `models/sample_data.py`

### 4.4 — Comments & Collaboration ✅

*Completed: 2026-02-26*

- **New page:** `pages/comments.py` at `/comments` — task comment management
- Task selector dropdown to view/add comments per task
- Comment thread display with author, timestamp, body
- Add/edit/delete comments with OBO author tracking
- **New component:** `components/comment_thread.py` — reusable comment thread UI
- **New services:** `services/comment_service.py` — `create_comment_from_form()`, `update_comment_from_form()`, `delete_comment()`
- **New repos:** `repositories/comment_repo.py` — full CRUD with task_id filtering
- **New validators:** `validate_comment_create()` in `utils/validators.py`
- **Enhanced repos:** `repositories/task_repo.py` — added `get_all_tasks()` for comment task selector
- **Enhanced services:** `services/task_service.py` — added `get_tasks()` passthrough
- **Sample data:** 5 comments across 3 tasks
- **Nav:** Added Comments link to sidebar under EXECUTION
- **Files:** `pages/comments.py` (new), `components/comment_thread.py` (new), `services/comment_service.py` (new), `repositories/comment_repo.py` (new), `repositories/task_repo.py`, `services/task_service.py`, `utils/validators.py`, `models/sample_data.py`, `app.py`

### 4.5 — Time Tracking ✅

*Completed: 2026-02-26*

- **New page:** `pages/timesheet.py` at `/timesheet` — time entry management
- Log hours per task with date, notes
- Hours-by-task summary chart (horizontal bar)
- Date range filter, task filter
- 4 KPI cards: Total Hours, Entries This Week, Avg Hours/Entry, Active Contributors
- **New services:** `services/time_entry_service.py` — `create_time_entry_from_form()`, `update_time_entry_from_form()`, `delete_time_entry()`
- **New repos:** `repositories/time_entry_repo.py` — full CRUD with task JOIN for titles
- **New validators:** `validate_time_entry_create()` in `utils/validators.py`
- **Sample data:** 10 time entries across tasks and users
- **Nav:** Added Timesheet link to sidebar under EXECUTION
- **Files:** `pages/timesheet.py` (new), `services/time_entry_service.py` (new), `repositories/time_entry_repo.py` (new), `utils/validators.py`, `models/sample_data.py`, `app.py`

### 4.6 — Resource Management Enhancements ✅

*Completed: 2026-02-26*

- **Resources page** (`pages/resources.py`): complete rewrite with assignment CRUD
- Team member assignment to projects (project_team CRUD)
- Allocation % management with over-allocation warnings (>100% total)
- Capacity planning view: who's available, who's overloaded
- Capacity chart (stacked bar by team member)
- Assignment create/edit/delete via crud_modal
- **New services:** `services/resource_service.py` — `get_capacity_overview()`, `get_over_allocated_members()`, `create_assignment_from_form()`, `update_assignment_from_form()`, `delete_assignment()`
- **Enhanced repos:** `repositories/resource_repo.py` — added `get_team_members()`, `get_project_team()`, `create_assignment()`, `update_assignment()`, `delete_assignment()`, `get_allocation_summary()`
- **New validators:** `validate_assignment_create()` in `utils/validators.py`
- **Sample data:** 4 team members, 6 project assignments
- **Files:** `pages/resources.py`, `services/resource_service.py` (new), `repositories/resource_repo.py`, `utils/validators.py`, `models/sample_data.py`

---

## Phase 5: Polish & Production Readiness ✅ COMPLETE

*Production hardening: export, auth, error handling, tests, notifications.*
*Completed: 2026-02-26 | PR #30 to develop*

### 5.1 — Export to Excel ✅

*Completed: 2026-02-26*

- Implemented `export_service.to_excel()` using openpyxl with auto-column-width, header formatting
- Wired export_button + download callback to 5 pages: risks, backlog, resources, reports, projects
- Added `openpyxl==3.1.5` to `requirements.txt`
- **Files:** `services/export_service.py`, `pages/risks.py`, `pages/backlog.py`, `pages/resources.py`, `pages/reports.py`, `pages/projects.py`, `requirements.txt`

### 5.2 — Auth & RBAC Enforcement ✅

*Completed: 2026-02-26*

- Implemented `has_permission()` with role hierarchy: admin (100), lead/pm (80), engineer (50), viewer (20)
- Operation levels: read (20), comment/create/update (50), delete/approve (80), admin (100)
- Entity-specific overrides: engineers can only CRUD tasks, comments, time_entries, retro_items
- All 13 service files gated with permission checks on write operations
- All page files conditionally show/hide create/edit/delete buttons based on user role
- Department-scoped data visibility via `can_access_department()`
- Local dev defaults to admin role for convenience
- **Files:** `services/auth_service.py`, all `services/*.py`, all `pages/*.py`, `models/sample_data.py`

### 5.3 — Specific Exception Handling ✅

*Completed: 2026-02-26*

- Replaced broad `except Exception` in `unity_catalog.py` with Databricks-specific exceptions (`ServerOperationError`, `OperationalError`, `DatabaseError`)
- Added `ImportError` guard for local dev (falls back to `Exception`)
- Switched to `cursor.fetchall_arrow().to_pandas()` for Arrow-native data transfer
- Added warehouse_id validation with descriptive `ConnectionError`
- Each exception type gets distinct log message for better diagnostics
- **Files:** `db/unity_catalog.py`

### 5.4 — Test Coverage ✅

*Completed: 2026-02-26*

- **325 tests total**, all passing
- Service layer tests: `test_task_service.py` (11), `test_sprint_service.py` (10), `test_charter_service.py` (14), `test_risk_service.py` (17), `test_project_service.py` (16), `test_portfolio_service.py` (11)
- Validator tests: `test_validators.py` (45+ tests covering all validators and edge cases)
- Repository tests: `test_base_repo.py` (8), `test_task_repo.py` (8), `test_sprint_repo.py` (6)
- Syntax validation: `test_syntax.py` — parametrized AST validation of ALL `.py` files
- Test infrastructure: `conftest.py` with `reset_sample_data` autouse fixture
- **Files:** `tests/conftest.py`, `tests/test_services/` (7 files), `tests/test_repositories/` (3 files), `tests/test_pages/test_syntax.py`

### 5.5 — Notification System ✅

*Completed: 2026-02-26*

- **New repo:** `repositories/notification_repo.py` — full CRUD with parameterized queries (get, create, mark_read, mark_all_read, get_unread_count, delete)
- **New component:** `components/notification_bell.py` — bell icon with unread count badge, dropdown panel, 30s auto-refresh interval
- **New callbacks:** `callbacks/notification_callbacks.py` — 3 callbacks: update_badge, load_notifications, mark_all_read
- Enhanced `services/notification_service.py` — `notify()`, `get_notifications()`, `mark_all_read()`, `get_unread_count()`
- Added `notifications` table to `models/schema_ddl.sql` and sample data (5 seed notifications)
- Integrated notification bell into topbar (`app.py`)
- Registered notification callbacks in `callbacks/__init__.py`
- **Files:** `repositories/notification_repo.py` (new), `components/notification_bell.py` (new), `callbacks/notification_callbacks.py` (new), `services/notification_service.py`, `repositories/base.py`, `models/schema_ddl.sql`, `models/sample_data.py`, `app.py`, `callbacks/__init__.py`

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
- **Phase 3** (Navigation & Multi-Dept) ✅ → organizational hierarchy, drill-down, filtering
- **Phase 4** (PMI Features) ✅ → PMBOK 7 knowledge area coverage (6 sub-tasks, 3 new pages, 3 page rewrites)
- **Phase 5** (Polish) ✅ → production hardening (export, RBAC, error handling, tests, notifications)

Each phase ends with a `/review-all` cycle.

---

## Post-Production: Configuration Parameterization

*Completed: 2026-02-27*

### Parameterize Unity Catalog Catalog/Schema References

Removed all hardcoded `workspace.project_management` references from runtime code. Catalog and schema are now configurable via `UC_CATALOG` and `UC_SCHEMA` environment variables (defaults: `workspace` / `project_management`).

**Changes:**
- **`db/unity_catalog.py`** — `get_connection()` now passes `catalog=settings.uc_catalog` and `schema=settings.uc_schema` to `sql.connect()`, ensuring bare table names resolve to the correct Unity Catalog location. Also reads `warehouse_id` from settings for consistency.
- **`repositories/notification_repo.py`** — Removed hardcoded `workspace.project_management.notifications` prefix; now uses bare `notifications` table name like all other repos.
- **`app.py`** — Sidebar footer now reads catalog/schema from settings instead of hardcoded string.
- **`app.yaml`** — Added `UC_CATALOG` and `UC_SCHEMA` env vars for deployment configuration.
- **Documentation** — Updated CLAUDE.md, architecture-plan.md, README.md with new configuration convention.

**Pattern established:** All SQL uses bare table names (e.g., `FROM portfolios`). The connection layer sets the default catalog/schema from settings. No runtime code references a specific catalog or schema name.

---

## Phase 6: UI Modernization — Glassmorphism Design + Icons ✅ COMPLETE

*Modern Linear/Vercel-inspired glassmorphism aesthetic with locally bundled Bootstrap Icons.*
*Completed: 2026-02-27*

### 6.1 — Bundle Bootstrap Icons + SLATE Theme Locally ✅

*Completed: 2026-02-27*

- Downloaded Bootstrap Icons v1.11.3 CSS + WOFF2/WOFF font files to `assets/bootstrap-icons/`
- Downloaded Bootswatch SLATE theme to `assets/slate/bootstrap.min.css`
- Removed CDN dependency (`external_stylesheets=[]` in `app.py`) — fully offline-capable
- Dash auto-loads all CSS from `assets/` — no code changes needed
- **Files:** `assets/bootstrap-icons/bootstrap-icons.min.css`, `assets/bootstrap-icons/fonts/*.woff*`, `assets/slate/bootstrap.min.css`, `app.py`

### 6.2 — Glassmorphism Design System (custom.css) ✅

*Completed: 2026-02-27*

- Created `assets/custom.css` (~280 lines) with CSS custom properties (design tokens)
- **Header fix:** `.page-title` left-aligned, `.page-header` flex container with icon box
- **Glass cards:** `backdrop-filter: blur(12px)`, `rgba()` backgrounds, subtle borders, hover lift
- **KPI cards:** Icon wrapper with 7 color variants, hover animation
- **Sidebar:** Glass background, accent left-border on active state
- **Tables:** Transparent backgrounds, hover tint, uppercase headers
- **Modals:** Glass background with deeper blur
- **Inputs:** Dark background, accent focus glow
- **Scrollbar:** Thin, translucent custom scrollbar
- **Files:** `assets/custom.css`

### 6.3 — Component Updates (Backward Compatible) ✅

*Completed: 2026-02-27*

- **`charts/theme.py`:** Background color darkened (`#0f1218` → `#0a0d12`), added `ICON_COLORS` dict
- **`components/kpi_card.py`:** Added optional `icon` and `icon_color` params — renders Bootstrap Icon in styled wrapper
- **`components/empty_state.py`:** Added optional `icon` param — renders large dim icon above message
- **`components/export_button.py`:** Added `bi-download` icon before label text
- All changes backward compatible — existing calls without new params unchanged
- **Files:** `charts/theme.py`, `components/kpi_card.py`, `components/empty_state.py`, `components/export_button.py`

### 6.4 — Page Header Icons + KPI Card Icons (16 Pages) ✅

*Completed: 2026-02-27*

- All 16 pages updated with `.page-header` div wrapping title + icon
- All KPI cards updated with contextual Bootstrap Icons and color-coded wrappers
- Icon mapping: dashboard (grid-1x2-fill), portfolios (collection-fill), roadmap (calendar-range-fill), projects (kanban-fill), charters (file-earmark-text-fill), gantt (bar-chart-steps), sprint (view-stacked), my_work (person-check-fill), backlog (list-check), retros (arrow-repeat), reports (graph-up-arrow), resources (people-fill), risks (shield-exclamation), deliverables (box-seam-fill), comments (chat-dots), timesheet (clock-history)
- **Files:** All 16 `pages/*.py`

---

## Phase 7: Full-Width Layout, Larger Typography & UX Improvements ✅ COMPLETE

*Wider layout, larger fonts, even KPI distribution, bigger health chart.*
*Completed: 2026-03-01*

### 7.1 — CSS Typography & Layout Updates ✅

*Completed: 2026-03-01*

- `.page-content` max-width: 1600px → 1800px for better 1920px monitor coverage
- `.page-content` padding: 24px → 24px 32px (wider horizontal breathing room)
- `.kpi-value` font-size: 1.5rem → 1.85rem (larger KPI numbers)
- `.kpi-label` font-size: 0.75rem → 0.85rem (more readable labels)
- `.kpi-sub` font-size: 0.75rem → 0.8rem
- `.card-header` font-size: 0.85rem → 0.9rem
- `.table-dark thead th` font-size: 0.7rem → 0.78rem (minimum readable)
- `.page-subtitle` font-size: 0.9rem → 1rem
- `.badge` font-size: 0.7rem → 0.75rem
- `.kpi-card .card-body` padding: 16px 20px → 20px 24px
- `.kpi-icon-wrapper` size: 36px → 40px, font-size: 1.1rem → 1.25rem
- **Files:** `assets/custom.css`

### 7.2 — Dashboard Layout Fix ✅

*Completed: 2026-03-01*

- KPI row: uneven `[2,2,2,3,3]` widths → all `md=True` (equal flex distribution)
- Health chart/portfolio split: `width=4`/`width=8` → `md=5`/`md=7` (larger chart)
- Health chart height: 300px → 380px
- Added `h-100` to chart card for same-row height matching
- Used `md` breakpoints for graceful tablet stacking
- **Files:** `pages/dashboard.py`

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
