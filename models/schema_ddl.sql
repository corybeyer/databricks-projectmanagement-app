-- ============================================================
-- PM Hub — Unity Catalog Schema DDL
-- ============================================================
-- Catalog: workspace
-- Schema:  project_management
-- Format:  Delta (time travel enabled on all tables)
-- ============================================================

CREATE SCHEMA IF NOT EXISTS workspace.project_management
COMMENT 'Portfolio & Project Management — Hybrid Waterfall/Agile';

USE workspace.project_management;

-- ─── PORTFOLIOS ────────────────────────────────────────────
-- Top-level grouping of related projects by strategic theme
CREATE TABLE IF NOT EXISTS portfolios (
    portfolio_id        STRING      NOT NULL    COMMENT 'PK — UUID',
    name                STRING      NOT NULL    COMMENT 'Portfolio display name',
    description         STRING                  COMMENT 'Strategic description',
    owner               STRING      NOT NULL    COMMENT 'Portfolio manager / owner',
    status              STRING      NOT NULL    COMMENT 'active | on_hold | archived',
    health              STRING      NOT NULL    COMMENT 'green | yellow | red',
    budget_total        DOUBLE                  COMMENT 'Total portfolio budget',
    strategic_priority  INT                     COMMENT 'Rank 1-N for prioritization',
    created_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    updated_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    is_deleted          BOOLEAN     NOT NULL    DEFAULT false,
    deleted_at          TIMESTAMP                             COMMENT 'When soft-deleted',

    CONSTRAINT pk_portfolios PRIMARY KEY (portfolio_id)
)
COMMENT 'Strategic portfolios grouping related projects'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');


-- ─── PROJECTS ──────────────────────────────────────────────
-- Individual projects within portfolios
CREATE TABLE IF NOT EXISTS projects (
    project_id          STRING      NOT NULL    COMMENT 'PK — UUID',
    portfolio_id        STRING      NOT NULL    COMMENT 'FK → portfolios',
    name                STRING      NOT NULL    COMMENT 'Project display name',
    description         STRING                  COMMENT 'Project description',
    owner               STRING      NOT NULL    COMMENT 'Project manager',
    sponsor             STRING                  COMMENT 'Executive sponsor',
    status              STRING      NOT NULL    COMMENT 'planning | active | on_hold | complete | cancelled',
    health              STRING      NOT NULL    COMMENT 'green | yellow | red',
    delivery_method     STRING      NOT NULL    COMMENT 'waterfall | agile | hybrid',
    current_phase_id    STRING                  COMMENT 'FK → phases — active phase',
    priority_rank       INT                     COMMENT 'Priority within portfolio',
    pct_complete        DOUBLE                  COMMENT 'Overall % complete 0-100',
    budget_total        DOUBLE                  COMMENT 'Approved budget',
    budget_spent        DOUBLE                  COMMENT 'Actual spend to date',
    start_date          DATE        NOT NULL    COMMENT 'Project start date',
    target_date         DATE                    COMMENT 'Target completion date',
    actual_end_date     DATE                    COMMENT 'Actual completion date',
    created_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    updated_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    is_deleted          BOOLEAN     NOT NULL    DEFAULT false,
    deleted_at          TIMESTAMP                             COMMENT 'When soft-deleted',

    CONSTRAINT pk_projects PRIMARY KEY (project_id),
    CONSTRAINT fk_projects_portfolio FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id)
)
COMMENT 'Individual projects within portfolios'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');


-- ─── PROJECT CHARTERS ──────────────────────────────────────
-- Formal project charter documents (one per project)
CREATE TABLE IF NOT EXISTS project_charters (
    charter_id          STRING      NOT NULL    COMMENT 'PK — UUID',
    project_id          STRING      NOT NULL    COMMENT 'FK → projects (1:1)',
    version             INT         NOT NULL    DEFAULT 1 COMMENT 'Charter version number',
    business_case       STRING      NOT NULL    COMMENT 'Why this project exists',
    objectives          STRING      NOT NULL    COMMENT 'SMART objectives (newline-separated)',
    scope_in            STRING      NOT NULL    COMMENT 'What IS included',
    scope_out           STRING      NOT NULL    COMMENT 'What is NOT included',
    assumptions         STRING                  COMMENT 'Key assumptions',
    constraints         STRING                  COMMENT 'Known constraints',
    stakeholders        STRING      NOT NULL    COMMENT 'Key stakeholders and roles',
    success_criteria    STRING      NOT NULL    COMMENT 'How we measure success',
    risks               STRING                  COMMENT 'Initial risk summary',
    budget              STRING                  COMMENT 'Approved budget amount',
    timeline            STRING                  COMMENT 'High-level timeline',
    delivery_method     STRING      NOT NULL    COMMENT 'waterfall | agile | hybrid + justification',
    approved_by         STRING                  COMMENT 'Approver name / title',
    approved_date       DATE                    COMMENT 'Formal approval date',
    created_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    updated_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    is_deleted          BOOLEAN     NOT NULL    DEFAULT false,
    deleted_at          TIMESTAMP                             COMMENT 'When soft-deleted',

    CONSTRAINT pk_charters PRIMARY KEY (charter_id),
    CONSTRAINT fk_charters_project FOREIGN KEY (project_id) REFERENCES projects(project_id)
)
COMMENT 'Formal project charter documents — one per project'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');


-- ─── PHASES ────────────────────────────────────────────────
-- Waterfall phases within a project (used in waterfall & hybrid)
CREATE TABLE IF NOT EXISTS phases (
    phase_id            STRING      NOT NULL    COMMENT 'PK — UUID',
    project_id          STRING      NOT NULL    COMMENT 'FK → projects',
    name                STRING      NOT NULL    COMMENT 'Phase name (e.g., Initiation, Design, Build)',
    phase_type          STRING      NOT NULL    COMMENT 'initiation | planning | design | build | test | deploy | closeout',
    phase_order         INT         NOT NULL    COMMENT 'Sequence number within project',
    delivery_method     STRING      NOT NULL    COMMENT 'waterfall | agile — method for THIS phase',
    status              STRING      NOT NULL    COMMENT 'not_started | active | complete',
    start_date          DATE                    COMMENT 'Planned start',
    end_date            DATE                    COMMENT 'Planned end',
    actual_start        DATE                    COMMENT 'Actual start',
    actual_end          DATE                    COMMENT 'Actual end',
    pct_complete        DOUBLE      DEFAULT 0   COMMENT 'Phase % complete',
    created_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    updated_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    is_deleted          BOOLEAN     NOT NULL    DEFAULT false,
    deleted_at          TIMESTAMP                             COMMENT 'When soft-deleted',

    CONSTRAINT pk_phases PRIMARY KEY (phase_id),
    CONSTRAINT fk_phases_project FOREIGN KEY (project_id) REFERENCES projects(project_id)
)
COMMENT 'Waterfall phases — used in waterfall and hybrid projects';


-- ─── GATES ─────────────────────────────────────────────────
-- Phase gate checkpoints (approval to proceed to next phase)
CREATE TABLE IF NOT EXISTS gates (
    gate_id             STRING      NOT NULL    COMMENT 'PK — UUID',
    phase_id            STRING      NOT NULL    COMMENT 'FK → phases — gate sits at END of phase',
    gate_order          INT         NOT NULL    COMMENT 'Gate sequence number',
    name                STRING      NOT NULL    COMMENT 'Gate name (e.g., Gate 1: Planning Approval)',
    status              STRING      NOT NULL    COMMENT 'pending | approved | rejected | deferred',
    criteria            STRING                  COMMENT 'What must be true to pass this gate',
    decision            STRING                  COMMENT 'Approval decision notes',
    decided_by          STRING                  COMMENT 'Who approved / rejected',
    decided_at          TIMESTAMP               COMMENT 'When decision was made',
    created_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    updated_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    is_deleted          BOOLEAN     NOT NULL    DEFAULT false,
    deleted_at          TIMESTAMP                             COMMENT 'When soft-deleted',

    CONSTRAINT pk_gates PRIMARY KEY (gate_id),
    CONSTRAINT fk_gates_phase FOREIGN KEY (phase_id) REFERENCES phases(phase_id)
)
COMMENT 'Phase gate approvals — waterfall governance checkpoints';


-- ─── DELIVERABLES ──────────────────────────────────────────
-- Formal deliverables tied to waterfall phases
CREATE TABLE IF NOT EXISTS deliverables (
    deliverable_id      STRING      NOT NULL    COMMENT 'PK — UUID',
    phase_id            STRING      NOT NULL    COMMENT 'FK → phases',
    name                STRING      NOT NULL    COMMENT 'Deliverable name',
    description         STRING                  COMMENT 'What this deliverable is',
    status              STRING      NOT NULL    COMMENT 'not_started | in_progress | complete | approved',
    owner               STRING                  COMMENT 'Responsible person',
    due_date            DATE                    COMMENT 'Expected completion',
    completed_date      DATE                    COMMENT 'Actual completion',
    artifact_url        STRING                  COMMENT 'Link to document / artifact',
    created_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    updated_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    is_deleted          BOOLEAN     NOT NULL    DEFAULT false,
    deleted_at          TIMESTAMP                             COMMENT 'When soft-deleted',

    CONSTRAINT pk_deliverables PRIMARY KEY (deliverable_id),
    CONSTRAINT fk_deliverables_phase FOREIGN KEY (phase_id) REFERENCES phases(phase_id)
)
COMMENT 'Formal deliverables within waterfall phases';


-- ─── SPRINTS ───────────────────────────────────────────────
-- Agile sprints (used in agile & hybrid projects)
CREATE TABLE IF NOT EXISTS sprints (
    sprint_id           STRING      NOT NULL    COMMENT 'PK — UUID',
    project_id          STRING      NOT NULL    COMMENT 'FK → projects',
    phase_id            STRING                  COMMENT 'FK → phases — which phase this sprint belongs to (hybrid)',
    name                STRING      NOT NULL    COMMENT 'Sprint name (e.g., Sprint 4)',
    goal                STRING                  COMMENT 'Sprint goal statement',
    start_date          DATE        NOT NULL    COMMENT 'Sprint start',
    end_date            DATE        NOT NULL    COMMENT 'Sprint end',
    status              STRING      NOT NULL    COMMENT 'planning | active | review | closed',
    capacity_points     INT                     COMMENT 'Team committed capacity',
    created_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    updated_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    is_deleted          BOOLEAN     NOT NULL    DEFAULT false,
    deleted_at          TIMESTAMP                             COMMENT 'When soft-deleted',

    CONSTRAINT pk_sprints PRIMARY KEY (sprint_id),
    CONSTRAINT fk_sprints_project FOREIGN KEY (project_id) REFERENCES projects(project_id),
    CONSTRAINT fk_sprints_phase FOREIGN KEY (phase_id) REFERENCES phases(phase_id)
)
COMMENT 'Agile sprints — linked to phases in hybrid projects';


-- ─── TASKS ─────────────────────────────────────────────────
-- Work items: epics, stories, tasks, bugs, subtasks
CREATE TABLE IF NOT EXISTS tasks (
    task_id             STRING      NOT NULL    COMMENT 'PK — UUID',
    project_id          STRING      NOT NULL    COMMENT 'FK → projects',
    phase_id            STRING                  COMMENT 'FK → phases (waterfall/hybrid context)',
    sprint_id           STRING                  COMMENT 'FK → sprints (null = backlog)',
    parent_task_id      STRING                  COMMENT 'FK → tasks (self-ref for hierarchy)',
    title               STRING      NOT NULL    COMMENT 'Task title',
    description         STRING                  COMMENT 'Detailed description',
    task_type           STRING      NOT NULL    COMMENT 'epic | story | task | bug | subtask',
    status              STRING      NOT NULL    COMMENT 'backlog | todo | in_progress | review | done',
    priority            STRING      NOT NULL    COMMENT 'critical | high | medium | low',
    assignee            STRING                  COMMENT 'FK → team_members.user_id',
    story_points        INT                     COMMENT 'Estimation points',
    due_date            DATE                    COMMENT 'Due date',
    backlog_rank        DOUBLE                  COMMENT 'Ordering rank (float for insert-between)',
    created_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    updated_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    is_deleted          BOOLEAN     NOT NULL    DEFAULT false,
    deleted_at          TIMESTAMP                             COMMENT 'When soft-deleted',

    CONSTRAINT pk_tasks PRIMARY KEY (task_id),
    CONSTRAINT fk_tasks_project FOREIGN KEY (project_id) REFERENCES projects(project_id),
    CONSTRAINT fk_tasks_sprint FOREIGN KEY (sprint_id) REFERENCES sprints(sprint_id),
    CONSTRAINT fk_tasks_phase FOREIGN KEY (phase_id) REFERENCES phases(phase_id)
)
COMMENT 'Work items — epic/story/task/bug hierarchy'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');


-- ─── STATUS TRANSITIONS ───────────────────────────────────
-- Audit log of every status change (for cycle time analytics)
CREATE TABLE IF NOT EXISTS status_transitions (
    transition_id       STRING      NOT NULL    COMMENT 'PK — UUID',
    task_id             STRING      NOT NULL    COMMENT 'FK → tasks',
    from_status         STRING      NOT NULL    COMMENT 'Previous status',
    to_status           STRING      NOT NULL    COMMENT 'New status',
    changed_by          STRING      NOT NULL    COMMENT 'Who made the change',
    transitioned_at     TIMESTAMP   NOT NULL    COMMENT 'When the change occurred',
    created_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),

    CONSTRAINT pk_transitions PRIMARY KEY (transition_id),
    CONSTRAINT fk_transitions_task FOREIGN KEY (task_id) REFERENCES tasks(task_id)
)
COMMENT 'Status change audit log — powers cycle time and lead time analytics';


-- ─── COMMENTS ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS comments (
    comment_id          STRING      NOT NULL    COMMENT 'PK — UUID',
    task_id             STRING      NOT NULL    COMMENT 'FK → tasks',
    author              STRING      NOT NULL    COMMENT 'Comment author',
    body                STRING      NOT NULL    COMMENT 'Comment text',
    created_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    updated_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    is_deleted          BOOLEAN     NOT NULL    DEFAULT false,
    deleted_at          TIMESTAMP                             COMMENT 'When soft-deleted',

    CONSTRAINT pk_comments PRIMARY KEY (comment_id),
    CONSTRAINT fk_comments_task FOREIGN KEY (task_id) REFERENCES tasks(task_id)
)
COMMENT 'Task comments and discussion';


-- ─── TIME ENTRIES ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS time_entries (
    entry_id            STRING      NOT NULL    COMMENT 'PK — UUID',
    task_id             STRING      NOT NULL    COMMENT 'FK → tasks',
    user_id             STRING      NOT NULL    COMMENT 'FK → team_members',
    hours               DOUBLE      NOT NULL    COMMENT 'Hours logged',
    work_date           DATE        NOT NULL    COMMENT 'Date of work',
    notes               STRING                  COMMENT 'Work notes',
    created_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    updated_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),

    CONSTRAINT pk_time_entries PRIMARY KEY (entry_id),
    CONSTRAINT fk_time_task FOREIGN KEY (task_id) REFERENCES tasks(task_id)
)
COMMENT 'Time tracking entries';


-- ─── TEAM MEMBERS ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS team_members (
    user_id             STRING      NOT NULL    COMMENT 'PK — maps to Databricks identity',
    display_name        STRING      NOT NULL    COMMENT 'Display name',
    email               STRING      NOT NULL    COMMENT 'Email address',
    role                STRING      NOT NULL    COMMENT 'admin | lead | engineer | analyst | viewer',
    is_active           BOOLEAN     NOT NULL    DEFAULT true,
    capacity_pct        INT         DEFAULT 100 COMMENT 'Available capacity percentage (100=full time)',
    joined_at           TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    
    CONSTRAINT pk_team_members PRIMARY KEY (user_id)
)
COMMENT 'Team members — synced from Databricks workspace identity';


-- ─── PROJECT TEAM ASSIGNMENTS ──────────────────────────────
-- Many-to-many: which team members work on which projects
CREATE TABLE IF NOT EXISTS project_team (
    project_id          STRING      NOT NULL    COMMENT 'FK → projects',
    user_id             STRING      NOT NULL    COMMENT 'FK → team_members',
    project_role        STRING      NOT NULL    COMMENT 'pm | lead | engineer | analyst | stakeholder',
    allocation_pct      INT         NOT NULL    COMMENT 'Percentage of time allocated to this project',
    start_date          DATE                    COMMENT 'When assignment begins',
    end_date            DATE                    COMMENT 'When assignment ends',
    updated_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    is_deleted          BOOLEAN     NOT NULL    DEFAULT false,
    deleted_at          TIMESTAMP                             COMMENT 'When soft-deleted',

    CONSTRAINT pk_project_team PRIMARY KEY (project_id, user_id),
    CONSTRAINT fk_pt_project FOREIGN KEY (project_id) REFERENCES projects(project_id),
    CONSTRAINT fk_pt_member FOREIGN KEY (user_id) REFERENCES team_members(user_id)
)
COMMENT 'Project team assignments with allocation percentages';


-- ─── RISKS ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS risks (
    risk_id             STRING      NOT NULL    COMMENT 'PK — UUID',
    project_id          STRING      NOT NULL    COMMENT 'FK → projects',
    portfolio_id        STRING                  COMMENT 'FK → portfolios (for portfolio-level risks)',
    title               STRING      NOT NULL    COMMENT 'Risk title',
    description         STRING                  COMMENT 'Detailed description',
    category            STRING      NOT NULL    COMMENT 'scope | schedule | resource | technical | external',
    probability         INT         NOT NULL    COMMENT '1-5 scale',
    impact              INT         NOT NULL    COMMENT '1-5 scale',
    risk_score          INT         NOT NULL    COMMENT 'probability × impact (auto-calculated)',
    status              STRING      NOT NULL    COMMENT 'open | mitigating | accepted | closed',
    mitigation_plan     STRING                  COMMENT 'How we address this risk',
    owner               STRING                  COMMENT 'Risk owner',
    created_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    updated_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    is_deleted          BOOLEAN     NOT NULL    DEFAULT false,
    deleted_at          TIMESTAMP                             COMMENT 'When soft-deleted',

    CONSTRAINT pk_risks PRIMARY KEY (risk_id),
    CONSTRAINT fk_risks_project FOREIGN KEY (project_id) REFERENCES projects(project_id)
)
COMMENT 'Risk register — probability × impact scoring';


-- ─── RETRO ITEMS ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS retro_items (
    retro_id            STRING      NOT NULL    COMMENT 'PK — UUID',
    sprint_id           STRING      NOT NULL    COMMENT 'FK → sprints',
    author              STRING      NOT NULL    COMMENT 'Who submitted',
    category            STRING      NOT NULL    COMMENT 'went_well | improve | action_item',
    body                STRING      NOT NULL    COMMENT 'Retro item text',
    votes               INT         DEFAULT 0   COMMENT 'Team votes',
    action_task_id      STRING                  COMMENT 'FK → tasks (if action item becomes a task)',
    created_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    updated_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    is_deleted          BOOLEAN     NOT NULL    DEFAULT false,
    deleted_at          TIMESTAMP                             COMMENT 'When soft-deleted',

    CONSTRAINT pk_retros PRIMARY KEY (retro_id),
    CONSTRAINT fk_retros_sprint FOREIGN KEY (sprint_id) REFERENCES sprints(sprint_id)
)
COMMENT 'Sprint retrospective items — went well, improve, action items';


-- ─── DEPENDENCIES ──────────────────────────────────────────
-- Cross-project and cross-task dependencies
CREATE TABLE IF NOT EXISTS dependencies (
    dependency_id       STRING      NOT NULL    COMMENT 'PK — UUID',
    source_project_id   STRING      NOT NULL    COMMENT 'FK → projects — the blocking project',
    source_task_id      STRING                  COMMENT 'FK → tasks — specific blocking task (optional)',
    target_project_id   STRING      NOT NULL    COMMENT 'FK → projects — the blocked project',
    target_task_id      STRING                  COMMENT 'FK → tasks — specific blocked task (optional)',
    dependency_type     STRING      NOT NULL    COMMENT 'blocking | dependent | shared_resource | informational',
    risk_level          STRING      NOT NULL    COMMENT 'high | medium | low',
    description         STRING                  COMMENT 'What the dependency is',
    status              STRING      NOT NULL    COMMENT 'active | resolved | accepted',
    created_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    updated_at          TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    is_deleted          BOOLEAN     NOT NULL    DEFAULT false,
    deleted_at          TIMESTAMP                             COMMENT 'When soft-deleted',

    CONSTRAINT pk_dependencies PRIMARY KEY (dependency_id),
    CONSTRAINT fk_dep_source FOREIGN KEY (source_project_id) REFERENCES projects(project_id),
    CONSTRAINT fk_dep_target FOREIGN KEY (target_project_id) REFERENCES projects(project_id)
)
COMMENT 'Cross-project dependencies and blocking relationships';
