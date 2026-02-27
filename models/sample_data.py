"""
Sample Data — Local Development Fallback
==========================================
Returns realistic sample data when not connected to Databricks.
Each function returns a pd.DataFrame matching the UC table schema.

In-memory write mode: when USE_SAMPLE_DATA=true, CRUD operations
modify a module-level mutable store so local dev can test writes.
"""

import uuid
from datetime import datetime
from typing import Callable, Dict, Optional

import pandas as pd


# ---------------------------------------------------------------------------
# Mutable store — initialized lazily from read-only seed functions
# ---------------------------------------------------------------------------

_store: Dict[str, pd.DataFrame] = {}


def _get_store(table_name: str, initializer_fn: Callable[[], pd.DataFrame]) -> pd.DataFrame:
    """Lazy-init: first access copies the read-only sample data into mutable store.

    Ensures standard audit columns (created_at, updated_at, is_deleted) exist
    on all seeded DataFrames so filtering and optimistic locking work correctly.
    """
    if table_name not in _store:
        df = initializer_fn()
        if not df.empty:
            if "created_at" not in df.columns:
                df["created_at"] = "2026-01-01 00:00:00"
            if "updated_at" not in df.columns:
                df["updated_at"] = "2026-01-01 00:00:00"
            if "is_deleted" not in df.columns:
                df["is_deleted"] = False
        _store[table_name] = df
    return _store[table_name]


def reset_store() -> None:
    """Clear all mutable state. Called on app restart or in tests."""
    _store.clear()


# ---------------------------------------------------------------------------
# Generic CRUD helpers (operate on the mutable store)
# ---------------------------------------------------------------------------

_TABLE_ID_COLUMNS = {
    "departments": "department_id", "portfolios": "portfolio_id",
    "projects": "project_id", "project_charters": "charter_id",
    "phases": "phase_id", "gates": "gate_id", "deliverables": "deliverable_id",
    "sprints": "sprint_id", "tasks": "task_id", "status_transitions": "transition_id",
    "comments": "comment_id", "time_entries": "entry_id", "team_members": "user_id",
    "risks": "risk_id", "retro_items": "retro_id", "project_team": "user_id",
    "dependencies": "dependency_id", "audit_log": "audit_id",
    "notifications": "notification_id",
    "resource_allocations": "user_id", "portfolio_projects": "project_id",
    "velocity": "sprint_name", "burndown": "burn_date", "cycle_times": "task_id",
}


def create_record(
    table_name: str,
    record: dict,
    initializer_fn: Optional[Callable[[], pd.DataFrame]] = None,
) -> str:
    """Insert a new record into the in-memory store.

    - Auto-generates UUID for the primary key ({singular}_id) if not provided.
    - Sets created_at and updated_at to now.
    - Returns the new record's ID.
    """
    df = _get_store(table_name, initializer_fn or (lambda: pd.DataFrame()))

    # Generate ID if missing
    id_col = _TABLE_ID_COLUMNS.get(table_name, f"{table_name.rstrip('s')}_id")
    if id_col not in record or not record[id_col]:
        record[id_col] = str(uuid.uuid4())[:8]

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record.setdefault("created_at", now)
    record.setdefault("updated_at", now)
    record.setdefault("is_deleted", False)

    new_row = pd.DataFrame([record])
    _store[table_name] = pd.concat([df, new_row], ignore_index=True)
    return record[id_col]


def update_record(
    table_name: str,
    id_column: str,
    id_value: str,
    updates: dict,
    expected_updated_at: Optional[str] = None,
) -> bool:
    """Update a record in the in-memory store.

    - Supports optimistic locking via expected_updated_at.
    - Sets updated_at to now.
    - Returns True if updated, False if not found or conflict.
    """
    if table_name not in _store:
        init_fn = _get_table_initializer(table_name)
        if init_fn:
            _get_store(table_name, init_fn)
        else:
            return False
    df = _store[table_name]

    # Build mask: match ID and not soft-deleted
    mask = df[id_column] == id_value
    if "is_deleted" in df.columns:
        mask = mask & (df["is_deleted"] == False)  # noqa: E712
    if mask.sum() == 0:
        return False

    # Optimistic lock check
    if expected_updated_at is not None and "updated_at" in df.columns:
        current = df.loc[mask, "updated_at"].iloc[0]
        if str(current) != str(expected_updated_at):
            return False

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updates["updated_at"] = now
    for col, val in updates.items():
        if col in df.columns:
            df.loc[mask, col] = val
    return True


def delete_record(
    table_name: str,
    id_column: str,
    id_value: str,
    user_email: Optional[str] = None,
) -> bool:
    """Soft-delete a record (set is_deleted=True, deleted_at=now).

    Returns True if deleted, False if not found.
    """
    if table_name not in _store:
        init_fn = _get_table_initializer(table_name)
        if init_fn:
            _get_store(table_name, init_fn)
        else:
            return False
    df = _store[table_name]

    mask = df[id_column] == id_value
    if "is_deleted" in df.columns:
        mask = mask & (df["is_deleted"] == False)  # noqa: E712
    if mask.sum() == 0:
        return False

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df.loc[mask, "is_deleted"] = True
    if "deleted_at" in df.columns:
        df.loc[mask, "deleted_at"] = now
    if "deleted_by" in df.columns and user_email:
        df.loc[mask, "deleted_by"] = user_email
    df.loc[mask, "updated_at"] = now
    return True


# ---------------------------------------------------------------------------
# Seed data initializers (read-only originals)
# ---------------------------------------------------------------------------

def _init_departments() -> pd.DataFrame:
    return pd.DataFrame([
        {"department_id": "dept-001", "name": "Data Engineering", "description": "Data platform, pipelines, and infrastructure",
         "parent_dept_id": None, "head": "u-001", "parent_name": None},
        {"department_id": "dept-002", "name": "Finance Analytics", "description": "Financial reporting and analytics",
         "parent_dept_id": None, "head": "u-003", "parent_name": None},
        {"department_id": "dept-003", "name": "Platform Engineering", "description": "Developer tools and platforms",
         "parent_dept_id": "dept-001", "head": "u-002", "parent_name": "Data Engineering"},
    ])


def _init_portfolios() -> pd.DataFrame:
    return pd.DataFrame([
        {"portfolio_id": "pf-001", "name": "Data Platform Modernization", "owner": "Cory S.",
         "department_id": "dept-001",
         "status": "active", "health": "yellow", "project_count": 5,
         "avg_completion": 58, "total_spent": 792000, "total_budget": 1100000,
         "description": "Modernize the enterprise data platform with Unity Catalog, DLT, and governance tooling.",
         "strategic_priority": "Digital Transformation", "created_by": "cory@example.com"},
        {"portfolio_id": "pf-002", "name": "Financial Reporting & Analytics", "owner": "Cory S.",
         "department_id": "dept-002",
         "status": "active", "health": "green", "project_count": 4,
         "avg_completion": 64, "total_spent": 483800, "total_budget": 820000,
         "description": "Deliver end-to-end financial reporting from SAP/ERP through to self-service dashboards.",
         "strategic_priority": "Operational Excellence", "created_by": "cory@example.com"},
        {"portfolio_id": "pf-003", "name": "Self-Service & Applications", "owner": "Cory S.",
         "department_id": "dept-001",
         "status": "active", "health": "green", "project_count": 3,
         "avg_completion": 42, "total_spent": 182400, "total_budget": 480000,
         "description": "Build self-service analytics tools and internal applications for the data team.",
         "strategic_priority": "Team Enablement", "created_by": "cory@example.com"},
    ])


def _init_portfolio_projects() -> pd.DataFrame:
    return pd.DataFrame([
        {"project_id": "prj-001", "name": "Unity Catalog Migration", "status": "active",
         "delivery_method": "hybrid", "pct_complete": 55, "current_phase_name": "Build",
         "health": "yellow", "budget_total": 420000, "budget_spent": 302400,
         "active_sprint_name": "Sprint 4", "start_date": "2026-01-06", "target_date": "2026-08-01",
         "portfolio_name": "Data Platform Modernization", "portfolio_id": "pf-001",
         "owner": "Cory S.", "sponsor": "VP Data & Analytics",
         "department_id": "dept-001", "created_by": "cory@example.com"},
        {"project_id": "prj-002", "name": "DLT Pipeline Framework", "status": "active",
         "delivery_method": "agile", "pct_complete": 72, "current_phase_name": "Build",
         "health": "green", "budget_total": 320000, "budget_spent": 230400,
         "active_sprint_name": "Sprint 6", "start_date": "2026-01-13", "target_date": "2026-06-15",
         "portfolio_name": "Data Platform Modernization", "portfolio_id": "pf-001",
         "owner": "Chris J.", "sponsor": "VP Data & Analytics",
         "department_id": "dept-001", "created_by": "cory@example.com"},
        {"project_id": "prj-003", "name": "Secrets Management Rollout", "status": "active",
         "delivery_method": "waterfall", "pct_complete": 85, "current_phase_name": "UAT",
         "health": "green", "budget_total": 80000, "budget_spent": 68000,
         "active_sprint_name": None, "start_date": "2025-11-01", "target_date": "2026-03-15",
         "portfolio_name": "Data Platform Modernization", "portfolio_id": "pf-001",
         "owner": "Anna K.", "sponsor": "CIO",
         "department_id": "dept-001", "created_by": "cory@example.com"},
    ])


def _init_project_charter() -> pd.DataFrame:
    return pd.DataFrame([
        {"charter_id": "ch-001", "project_id": "prj-001",
         "project_name": "Unity Catalog Migration",
         "description": None,
         "business_case": "Migrate legacy Hive metastore to Unity Catalog for centralized governance, lineage tracking, and cross-workspace data sharing.",
         "objectives": "1. Migrate 100% of production tables to UC by Q2\n2. Implement domain-driven schema design\n3. Enable row-level security for Finance data\n4. Establish automated lineage tracking",
         "scope_in": "All production Databricks workspaces, Bronze/Silver/Gold layers, access policies, secrets management integration",
         "scope_out": "Legacy on-prem SQL Server databases, third-party tool migrations, Power BI semantic model changes",
         "stakeholders": "CIO (Sponsor), VP Data (Owner), Finance Dir (Key User), IT Security (Reviewer)",
         "success_criteria": "Zero data loss during migration, <2hr downtime per workspace, all access policies replicated, UAT sign-off from Finance",
         "risks": "Resource contention with DLT project, SAP BW schema changes mid-migration, team capacity constraints",
         "budget": "$420,000", "timeline": "Jan 2026 — Aug 2026",
         "delivery_method": "Hybrid — Waterfall phases with Agile sprint execution",
         "status": "approved", "version": 1,
         "approved_by": "VP Data & Analytics", "approved_date": "2025-12-15",
         "created_by": "cory@example.com", "updated_by": "cory@example.com"},
    ])


def _init_sprints() -> pd.DataFrame:
    return pd.DataFrame([
        {"sprint_id": "sp-001", "name": "Sprint 1", "status": "closed",
         "project_id": "prj-001", "goal": None,
         "start_date": "2026-01-20", "end_date": "2026-01-31",
         "total_points": 26, "done_points": 24, "capacity_points": 28},
        {"sprint_id": "sp-002", "name": "Sprint 2", "status": "closed",
         "project_id": "prj-001", "goal": None,
         "start_date": "2026-02-03", "end_date": "2026-02-14",
         "total_points": 30, "done_points": 28, "capacity_points": 30},
        {"sprint_id": "sp-003", "name": "Sprint 3", "status": "closed",
         "project_id": "prj-001", "goal": None,
         "start_date": "2026-02-17", "end_date": "2026-02-28",
         "total_points": 32, "done_points": 32, "capacity_points": 32},
        {"sprint_id": "sp-004", "name": "Sprint 4", "status": "active",
         "project_id": "prj-001", "goal": "Complete UC migration build phase",
         "start_date": "2026-03-02", "end_date": "2026-03-13",
         "total_points": 34, "done_points": 21, "capacity_points": 34},
    ])


def _init_tasks() -> pd.DataFrame:
    return pd.DataFrame([
        {"task_id": "t-001", "title": "P&L Bronze ingestion", "task_type": "story",
         "status": "done", "story_points": 8, "assignee_name": "Chris J.", "priority": "high",
         "project_id": "prj-001", "sprint_id": "sp-004", "assignee": "u-002",
         "description": None, "due_date": None},
        {"task_id": "t-002", "title": "DLT pipeline — Cost Centers", "task_type": "story",
         "status": "in_progress", "story_points": 8, "assignee_name": "Chris J.", "priority": "high",
         "project_id": "prj-001", "sprint_id": "sp-004", "assignee": "u-002",
         "description": None, "due_date": None},
        {"task_id": "t-003", "title": "SQL Server sync job", "task_type": "story",
         "status": "in_progress", "story_points": 5, "assignee_name": "Cory S.", "priority": "medium",
         "project_id": "prj-001", "sprint_id": "sp-004", "assignee": "u-001",
         "description": None, "due_date": None},
        {"task_id": "t-004", "title": "UAT comparison notebook", "task_type": "task",
         "status": "review", "story_points": 3, "assignee_name": "Chris J.", "priority": "medium",
         "project_id": "prj-001", "sprint_id": "sp-004", "assignee": "u-002",
         "description": None, "due_date": None},
        {"task_id": "t-005", "title": "Bronze→Silver GL mapping", "task_type": "story",
         "status": "todo", "story_points": 5, "assignee_name": "Cory S.", "priority": "high",
         "project_id": "prj-001", "sprint_id": "sp-004", "assignee": "u-001",
         "description": None, "due_date": None},
        {"task_id": "t-006", "title": "Secrets vault integration", "task_type": "task",
         "status": "todo", "story_points": 3, "assignee_name": None, "priority": "medium",
         "project_id": "prj-001", "sprint_id": "sp-004", "assignee": None,
         "description": None, "due_date": None},
        {"task_id": "t-007", "title": "Balance Sheet DLT", "task_type": "story",
         "status": "done", "story_points": 5, "assignee_name": "Anna K.", "priority": "high",
         "project_id": "prj-001", "sprint_id": "sp-004", "assignee": "u-003",
         "description": None, "due_date": None},
        {"task_id": "t-008", "title": "Access policy — Finance", "task_type": "task",
         "status": "done", "story_points": 2, "assignee_name": "Cory S.", "priority": "medium",
         "project_id": "prj-001", "sprint_id": "sp-004", "assignee": "u-001",
         "description": None, "due_date": None},
        {"task_id": "t-009", "title": "Data quality checks — Silver layer", "task_type": "story",
         "status": "backlog", "story_points": 5, "assignee_name": None, "priority": "medium",
         "project_id": "prj-001", "sprint_id": None, "assignee": None,
         "description": None, "due_date": None},
        {"task_id": "t-010", "title": "Lineage tracking POC", "task_type": "task",
         "status": "backlog", "story_points": 3, "assignee_name": None, "priority": "low",
         "project_id": "prj-001", "sprint_id": None, "assignee": None,
         "description": None, "due_date": None},
    ])


def _init_risks() -> pd.DataFrame:
    return pd.DataFrame([
        {"risk_id": "r-001", "project_id": "prj-001", "portfolio_id": "pf-001",
         "title": "SAP BW schema changes during migration",
         "project_name": "Unity Catalog Migration", "portfolio_name": "Data Platform Modernization",
         "category": "scope", "probability": 4, "impact": 4, "risk_score": 16,
         "status": "monitoring", "mitigation_plan": "Weekly sync with SAP team; maintain mapping layer",
         "response_strategy": "mitigate", "contingency_plan": "Freeze migration, revert to Hive metastore",
         "trigger_conditions": "SAP team announces schema change with <2 week notice",
         "risk_proximity": "near_term", "risk_urgency": 4,
         "residual_probability": 2, "residual_impact": 3, "residual_score": 6,
         "secondary_risks": "Mapping layer adds maintenance overhead",
         "identified_date": "2026-01-10", "last_review_date": "2026-02-20",
         "response_owner": "Chris J.", "owner": "Cory S."},
        {"risk_id": "r-002", "project_id": "prj-002", "portfolio_id": "pf-001",
         "title": "DLT framework version upgrade mid-sprint",
         "project_name": "DLT Pipeline Framework", "portfolio_name": "Data Platform Modernization",
         "category": "technical", "probability": 3, "impact": 3, "risk_score": 9,
         "status": "identified", "mitigation_plan": "Pin DLT version; test upgrades in staging first",
         "response_strategy": "avoid", "contingency_plan": "Roll back to previous DLT version",
         "trigger_conditions": "Databricks announces breaking DLT change in release notes",
         "risk_proximity": "mid_term", "risk_urgency": 2,
         "residual_probability": 1, "residual_impact": 2, "residual_score": 2,
         "secondary_risks": None,
         "identified_date": "2026-01-15", "last_review_date": "2026-02-18",
         "response_owner": "Chris J.", "owner": "Chris J."},
        {"risk_id": "r-003", "project_id": "prj-001", "portfolio_id": "pf-001",
         "title": "Team capacity constraints during Q2",
         "project_name": "Unity Catalog Migration", "portfolio_name": "Data Platform Modernization",
         "category": "resource", "probability": 3, "impact": 4, "risk_score": 12,
         "status": "response_planning", "mitigation_plan": "Cross-train analyst on migration tasks",
         "response_strategy": "mitigate", "contingency_plan": "Hire contractor for 3-month engagement",
         "trigger_conditions": "More than 1 team member unavailable for >1 week",
         "risk_proximity": "near_term", "risk_urgency": 3,
         "residual_probability": 2, "residual_impact": 3, "residual_score": 6,
         "secondary_risks": "Contractor ramp-up time; knowledge transfer overhead",
         "identified_date": "2026-02-01", "last_review_date": "2026-02-22",
         "response_owner": "Cory S.", "owner": "Cory S."},
    ])


def _init_team_members() -> pd.DataFrame:
    return pd.DataFrame([
        {"user_id": "u-001", "display_name": "Cory S.", "email": "cory@example.com",
         "department_id": "dept-001", "role": "admin", "is_active": True, "capacity_pct": 100},
        {"user_id": "u-002", "display_name": "Chris J.", "email": "chris@example.com",
         "department_id": "dept-001", "role": "lead", "is_active": True, "capacity_pct": 100},
        {"user_id": "u-003", "display_name": "Anna K.", "email": "anna@example.com",
         "department_id": "dept-002", "role": "engineer", "is_active": True, "capacity_pct": 100},
        {"user_id": "u-004", "display_name": "Jordan T.", "email": "jordan@example.com",
         "department_id": "dept-001", "role": "viewer", "is_active": True, "capacity_pct": 80},
    ])


def _init_project_team() -> pd.DataFrame:
    return pd.DataFrame([
        {"project_id": "prj-001", "user_id": "u-001", "project_role": "pm",
         "allocation_pct": 60, "start_date": "2026-01-06", "end_date": "2026-08-01",
         "created_by": "cory@example.com"},
        {"project_id": "prj-002", "user_id": "u-001", "project_role": "lead",
         "allocation_pct": 30, "start_date": "2026-01-13", "end_date": "2026-06-15",
         "created_by": "cory@example.com"},
        {"project_id": "prj-001", "user_id": "u-002", "project_role": "engineer",
         "allocation_pct": 80, "start_date": "2026-01-06", "end_date": "2026-08-01",
         "created_by": "cory@example.com"},
        {"project_id": "prj-002", "user_id": "u-003", "project_role": "analyst",
         "allocation_pct": 50, "start_date": "2026-01-13", "end_date": "2026-06-15",
         "created_by": "cory@example.com"},
        {"project_id": "prj-003", "user_id": "u-003", "project_role": "analyst",
         "allocation_pct": 40, "start_date": "2025-11-01", "end_date": "2026-03-15",
         "created_by": "cory@example.com"},
        {"project_id": "prj-001", "user_id": "u-004", "project_role": "engineer",
         "allocation_pct": 50, "start_date": "2026-02-01", "end_date": "2026-08-01",
         "created_by": "cory@example.com"},
    ])


def _init_resource_allocations() -> pd.DataFrame:
    return pd.DataFrame([
        {"user_id": "u-001", "display_name": "Cory S.", "role": "lead",
         "department_id": "dept-001",
         "project_name": "Unity Catalog Migration", "project_id": "prj-001",
         "task_count": 3, "points_assigned": 13, "points_done": 2, "allocation_pct": 60},
        {"user_id": "u-001", "display_name": "Cory S.", "role": "lead",
         "department_id": "dept-001",
         "project_name": "DLT Pipeline Framework", "project_id": "prj-002",
         "task_count": 1, "points_assigned": 5, "points_done": 3, "allocation_pct": 30},
        {"user_id": "u-002", "display_name": "Chris J.", "role": "engineer",
         "department_id": "dept-001",
         "project_name": "Unity Catalog Migration", "project_id": "prj-001",
         "task_count": 3, "points_assigned": 19, "points_done": 8, "allocation_pct": 80},
        {"user_id": "u-003", "display_name": "Anna K.", "role": "analyst",
         "department_id": "dept-002",
         "project_name": "DLT Pipeline Framework", "project_id": "prj-002",
         "task_count": 1, "points_assigned": 5, "points_done": 5, "allocation_pct": 50},
        {"user_id": "u-003", "display_name": "Anna K.", "role": "analyst",
         "department_id": "dept-002",
         "project_name": "Secrets Management Rollout", "project_id": "prj-003",
         "task_count": 2, "points_assigned": 6, "points_done": 4, "allocation_pct": 40},
    ])


def _init_project_detail() -> pd.DataFrame:
    return pd.DataFrame([
        {"project_id": "prj-001", "name": "Unity Catalog Migration", "status": "active",
         "delivery_method": "hybrid", "pct_complete": 55, "current_phase_name": "Build",
         "health": "yellow", "budget_total": 420000, "budget_spent": 302400,
         "portfolio_name": "Data Platform Modernization", "portfolio_id": "pf-001",
         "start_date": "2026-01-06", "target_date": "2026-08-01",
         "priority_rank": 1, "description": "Migrate legacy Hive metastore to Unity Catalog.",
         "owner": "Cory S.", "sponsor": "VP Data & Analytics",
         "department_id": "dept-001", "created_by": "cory@example.com"},
    ])


def _init_project_phases() -> pd.DataFrame:
    return pd.DataFrame([
        {"phase_id": "ph-001", "project_id": "prj-001", "name": "Initiation",
         "phase_type": "initiation", "delivery_method": "waterfall",
         "status": "done", "pct_complete": 100,
         "start_date": "2026-01-06", "end_date": "2026-01-17", "phase_order": 1,
         "task_count": 4, "done_count": 4,
         "created_by": "cory@example.com"},
        {"phase_id": "ph-002", "project_id": "prj-001", "name": "Planning",
         "phase_type": "planning", "delivery_method": "waterfall",
         "status": "done", "pct_complete": 100,
         "start_date": "2026-01-20", "end_date": "2026-02-07", "phase_order": 2,
         "task_count": 6, "done_count": 6,
         "created_by": "cory@example.com"},
        {"phase_id": "ph-003", "project_id": "prj-001", "name": "Build",
         "phase_type": "build", "delivery_method": "agile",
         "status": "in_progress", "pct_complete": 55,
         "start_date": "2026-02-10", "end_date": "2026-05-29", "phase_order": 3,
         "task_count": 18, "done_count": 10,
         "created_by": "cory@example.com"},
        {"phase_id": "ph-004", "project_id": "prj-001", "name": "UAT",
         "phase_type": "test", "delivery_method": "waterfall",
         "status": "not_started", "pct_complete": 0,
         "start_date": "2026-06-01", "end_date": "2026-07-10", "phase_order": 4,
         "task_count": 0, "done_count": 0,
         "created_by": "cory@example.com"},
        {"phase_id": "ph-005", "project_id": "prj-001", "name": "Deployment",
         "phase_type": "deploy", "delivery_method": "waterfall",
         "status": "not_started", "pct_complete": 0,
         "start_date": "2026-07-13", "end_date": "2026-08-01", "phase_order": 5,
         "task_count": 0, "done_count": 0,
         "created_by": "cory@example.com"},
    ])


def _init_velocity() -> pd.DataFrame:
    return pd.DataFrame([
        {"sprint_name": "Sprint 1", "committed_points": 26, "completed_points": 24,
         "capacity_points": 28, "start_date": "2026-01-20", "end_date": "2026-01-31"},
        {"sprint_name": "Sprint 2", "committed_points": 30, "completed_points": 28,
         "capacity_points": 30, "start_date": "2026-02-03", "end_date": "2026-02-14"},
        {"sprint_name": "Sprint 3", "committed_points": 32, "completed_points": 32,
         "capacity_points": 32, "start_date": "2026-02-17", "end_date": "2026-02-28"},
    ])


def _init_burndown() -> pd.DataFrame:
    return pd.DataFrame([
        {"burn_date": "2026-03-02", "remaining_points": 34, "total_points": 34},
        {"burn_date": "2026-03-03", "remaining_points": 32, "total_points": 34},
        {"burn_date": "2026-03-04", "remaining_points": 29, "total_points": 34},
        {"burn_date": "2026-03-05", "remaining_points": 27, "total_points": 34},
        {"burn_date": "2026-03-06", "remaining_points": 27, "total_points": 34},
        {"burn_date": "2026-03-07", "remaining_points": 25, "total_points": 34},
        {"burn_date": "2026-03-08", "remaining_points": 25, "total_points": 34},
        {"burn_date": "2026-03-09", "remaining_points": 21, "total_points": 34},
        {"burn_date": "2026-03-10", "remaining_points": 18, "total_points": 34},
        {"burn_date": "2026-03-11", "remaining_points": 13, "total_points": 34},
    ])


def _init_gate_status() -> pd.DataFrame:
    return pd.DataFrame([
        {"gate_id": "g-001", "phase_id": "ph-001", "name": "Initiation Gate",
         "phase_name": "Initiation", "status": "approved", "gate_order": 1,
         "criteria": "Charter approved, stakeholders identified, budget allocated",
         "decision": "All criteria met. Proceed to Planning.",
         "decided_by": "VP Data", "decided_at": "2026-01-17",
         "created_by": "cory@example.com"},
        {"gate_id": "g-002", "phase_id": "ph-002", "name": "Planning Gate",
         "phase_name": "Planning", "status": "approved", "gate_order": 2,
         "criteria": "WBS complete, schedule baselined, risk register populated",
         "decision": "Planning artifacts complete. Proceed to Build.",
         "decided_by": "VP Data", "decided_at": "2026-02-07",
         "created_by": "cory@example.com"},
        {"gate_id": "g-003", "phase_id": "ph-003", "name": "Build Gate",
         "phase_name": "Build", "status": "pending", "gate_order": 3,
         "criteria": "All migration tasks complete, integration tests pass, data validation clean",
         "decision": None, "decided_by": None, "decided_at": None,
         "created_by": "cory@example.com"},
        {"gate_id": "g-004", "phase_id": "ph-004", "name": "UAT Gate",
         "phase_name": "UAT", "status": "pending", "gate_order": 4,
         "criteria": "UAT sign-off from Finance, zero critical defects, performance benchmarks met",
         "decision": None, "decided_by": None, "decided_at": None,
         "created_by": "cory@example.com"},
    ])


def _init_cycle_times() -> pd.DataFrame:
    return pd.DataFrame([
        {"task_id": "t-001", "title": "P&L Bronze ingestion", "task_type": "story",
         "from_status": "todo", "hours_in_status": 4},
        {"task_id": "t-001", "title": "P&L Bronze ingestion", "task_type": "story",
         "from_status": "in_progress", "hours_in_status": 32},
        {"task_id": "t-001", "title": "P&L Bronze ingestion", "task_type": "story",
         "from_status": "review", "hours_in_status": 8},
        {"task_id": "t-007", "title": "Balance Sheet DLT", "task_type": "story",
         "from_status": "todo", "hours_in_status": 2},
        {"task_id": "t-007", "title": "Balance Sheet DLT", "task_type": "story",
         "from_status": "in_progress", "hours_in_status": 24},
        {"task_id": "t-007", "title": "Balance Sheet DLT", "task_type": "story",
         "from_status": "review", "hours_in_status": 6},
        {"task_id": "t-008", "title": "Access policy — Finance", "task_type": "task",
         "from_status": "todo", "hours_in_status": 1},
        {"task_id": "t-008", "title": "Access policy — Finance", "task_type": "task",
         "from_status": "in_progress", "hours_in_status": 16},
        {"task_id": "t-008", "title": "Access policy — Finance", "task_type": "task",
         "from_status": "review", "hours_in_status": 4},
    ])


def _init_retro_items() -> pd.DataFrame:
    return pd.DataFrame([
        {"retro_id": "ret-001", "sprint_id": "sp-003", "category": "went_well",
         "body": "DLT pipeline setup was smooth — reusable template pays off",
         "item_text": "DLT pipeline setup was smooth — reusable template pays off",
         "votes": 5, "author": "cory@example.com", "status": "open"},
        {"retro_id": "ret-002", "sprint_id": "sp-003", "category": "went_well",
         "body": "Good collaboration between data eng and finance BA",
         "item_text": "Good collaboration between data eng and finance BA",
         "votes": 3, "author": "chris@example.com", "status": "open"},
        {"retro_id": "ret-003", "sprint_id": "sp-003", "category": "improve",
         "body": "UAT environment setup took 2 days — need automation",
         "item_text": "UAT environment setup took 2 days — need automation",
         "votes": 4, "author": "chris@example.com", "status": "open"},
        {"retro_id": "ret-004", "sprint_id": "sp-003", "category": "improve",
         "body": "Story points for infra tasks are consistently underestimated",
         "item_text": "Story points for infra tasks are consistently underestimated",
         "votes": 3, "author": "cory@example.com", "status": "open"},
        {"retro_id": "ret-005", "sprint_id": "sp-003", "category": "action_item",
         "body": "Create Terraform module for UAT workspace provisioning",
         "item_text": "Create Terraform module for UAT workspace provisioning",
         "votes": 4, "author": "cory@example.com", "status": "open"},
        {"retro_id": "ret-006", "sprint_id": "sp-003", "category": "action_item",
         "body": "Add spike tasks for infra estimation research",
         "item_text": "Add spike tasks for infra estimation research",
         "votes": 2, "author": "chris@example.com", "status": "open"},
    ])


def _init_audit_log() -> pd.DataFrame:
    return pd.DataFrame([
        {"audit_id": "aud-001", "user_email": "cory@example.com", "action": "create",
         "entity_type": "task", "entity_id": "t-001", "field_changed": None,
         "old_value": None, "new_value": None, "details": "Created task: P&L Bronze ingestion",
         "created_at": "2026-02-01 09:00:00"},
        {"audit_id": "aud-002", "user_email": "chris@example.com", "action": "update",
         "entity_type": "task", "entity_id": "t-001", "field_changed": "status",
         "old_value": "todo", "new_value": "in_progress", "details": None,
         "created_at": "2026-02-03 10:30:00"},
        {"audit_id": "aud-003", "user_email": "chris@example.com", "action": "update",
         "entity_type": "task", "entity_id": "t-001", "field_changed": "status",
         "old_value": "in_progress", "new_value": "done", "details": None,
         "created_at": "2026-02-10 16:00:00"},
        {"audit_id": "aud-004", "user_email": "cory@example.com", "action": "approve",
         "entity_type": "gate", "entity_id": "g-002", "field_changed": "status",
         "old_value": "pending", "new_value": "approved", "details": "Planning phase gate approved",
         "created_at": "2026-02-07 14:00:00"},
    ])


def _init_deliverables() -> pd.DataFrame:
    return pd.DataFrame([
        {"deliverable_id": "del-001", "phase_id": "ph-001", "name": "Project Charter Document",
         "description": "Signed project charter with business case, objectives, and scope",
         "status": "approved", "owner": "Cory S.", "due_date": "2026-01-17",
         "completed_date": "2026-01-16", "artifact_url": "https://docs.example.com/charter-v1",
         "phase_name": "Initiation", "phase_type": "initiation",
         "created_by": "cory@example.com"},
        {"deliverable_id": "del-002", "phase_id": "ph-002", "name": "Migration Plan & Runbook",
         "description": "Detailed migration plan with table inventory, dependencies, and rollback procedures",
         "status": "complete", "owner": "Chris J.", "due_date": "2026-02-07",
         "completed_date": "2026-02-06", "artifact_url": "https://docs.example.com/migration-runbook",
         "phase_name": "Planning", "phase_type": "planning",
         "created_by": "cory@example.com"},
        {"deliverable_id": "del-003", "phase_id": "ph-003", "name": "Unity Catalog Schema Design",
         "description": "Domain-driven catalog/schema/table hierarchy design document",
         "status": "in_progress", "owner": "Cory S.", "due_date": "2026-03-15",
         "completed_date": None, "artifact_url": None,
         "phase_name": "Build", "phase_type": "execution",
         "created_by": "cory@example.com"},
        {"deliverable_id": "del-004", "phase_id": "ph-003", "name": "DLT Pipeline Templates",
         "description": "Reusable DLT pipeline templates for Bronze/Silver/Gold layers",
         "status": "in_progress", "owner": "Chris J.", "due_date": "2026-04-01",
         "completed_date": None, "artifact_url": None,
         "phase_name": "Build", "phase_type": "execution",
         "created_by": "chris@example.com"},
        {"deliverable_id": "del-005", "phase_id": "ph-004", "name": "UAT Test Results Report",
         "description": "Comprehensive UAT results with data validation, access policy testing, and sign-off",
         "status": "not_started", "owner": "Anna K.", "due_date": "2026-07-01",
         "completed_date": None, "artifact_url": None,
         "phase_name": "UAT", "phase_type": "testing",
         "created_by": "cory@example.com"},
    ])


def _init_dependencies() -> pd.DataFrame:
    return pd.DataFrame([
        {"dependency_id": "dep-001", "source_project_id": "prj-001",
         "source_task_id": "t-003", "target_project_id": "prj-003",
         "target_task_id": None, "dependency_type": "blocking",
         "risk_level": "high",
         "description": "Unity Catalog migration requires secrets vault integration from prj-003 to be complete before production deployment.",
         "status": "active",
         "source_project_name": "Unity Catalog Migration",
         "target_project_name": "Secrets Management Rollout",
         "created_by": "cory@example.com"},
        {"dependency_id": "dep-002", "source_project_id": "prj-002",
         "source_task_id": None, "target_project_id": "prj-001",
         "target_task_id": "t-002", "dependency_type": "dependent",
         "risk_level": "medium",
         "description": "DLT Pipeline Framework depends on UC catalog structure being finalized for pipeline registration.",
         "status": "active",
         "source_project_name": "DLT Pipeline Framework",
         "target_project_name": "Unity Catalog Migration",
         "created_by": "chris@example.com"},
        {"dependency_id": "dep-003", "source_project_id": "prj-001",
         "source_task_id": None, "target_project_id": "prj-002",
         "target_task_id": None, "dependency_type": "shared_resource",
         "risk_level": "medium",
         "description": "Chris J. is allocated to both projects — scheduling conflicts possible during Q2.",
         "status": "accepted",
         "source_project_name": "Unity Catalog Migration",
         "target_project_name": "DLT Pipeline Framework",
         "created_by": "cory@example.com"},
        {"dependency_id": "dep-004", "source_project_id": "prj-003",
         "source_task_id": None, "target_project_id": "prj-001",
         "target_task_id": None, "dependency_type": "informational",
         "risk_level": "low",
         "description": "Secrets Management security audit results will inform UC access policy design.",
         "status": "resolved",
         "source_project_name": "Secrets Management Rollout",
         "target_project_name": "Unity Catalog Migration",
         "created_by": "cory@example.com"},
    ])


def _init_comments() -> pd.DataFrame:
    return pd.DataFrame([
        {"comment_id": "cmt-001", "task_id": "t-001", "author": "cory@example.com",
         "body": "Bronze ingestion looks good. Verified row counts match source.",
         "created_by": "cory@example.com", "updated_by": "cory@example.com",
         "created_at": "2026-02-10 09:15:00", "updated_at": "2026-02-10 09:15:00"},
        {"comment_id": "cmt-002", "task_id": "t-001", "author": "chris@example.com",
         "body": "Added data quality checks on the P&L columns. All passing.",
         "created_by": "chris@example.com", "updated_by": "chris@example.com",
         "created_at": "2026-02-10 14:30:00", "updated_at": "2026-02-10 14:30:00"},
        {"comment_id": "cmt-003", "task_id": "t-002", "author": "chris@example.com",
         "body": "Cost center mapping is more complex than expected. May need an extra day.",
         "created_by": "chris@example.com", "updated_by": "chris@example.com",
         "created_at": "2026-02-12 10:00:00", "updated_at": "2026-02-12 10:00:00"},
        {"comment_id": "cmt-004", "task_id": "t-002", "author": "cory@example.com",
         "body": "Understood. Let me know if you need help with the SAP mapping table.",
         "created_by": "cory@example.com", "updated_by": "cory@example.com",
         "created_at": "2026-02-12 11:45:00", "updated_at": "2026-02-12 11:45:00"},
        {"comment_id": "cmt-005", "task_id": "t-003", "author": "cory@example.com",
         "body": "SQL Server sync job is running on schedule. Need to add error handling for timeouts.",
         "created_by": "cory@example.com", "updated_by": "cory@example.com",
         "created_at": "2026-02-14 16:20:00", "updated_at": "2026-02-14 16:20:00"},
    ])


def _init_time_entries() -> pd.DataFrame:
    return pd.DataFrame([
        {"entry_id": "te-001", "task_id": "t-001", "user_id": "u-002",
         "hours": 4.0, "work_date": "2026-02-20", "notes": "Bronze ingestion pipeline setup",
         "task_title": "P&L Bronze ingestion", "project_id": "prj-001",
         "created_by": "chris@example.com"},
        {"entry_id": "te-002", "task_id": "t-001", "user_id": "u-002",
         "hours": 6.0, "work_date": "2026-02-21", "notes": "Completed P&L ingestion testing",
         "task_title": "P&L Bronze ingestion", "project_id": "prj-001",
         "created_by": "chris@example.com"},
        {"entry_id": "te-003", "task_id": "t-002", "user_id": "u-002",
         "hours": 3.5, "work_date": "2026-02-22", "notes": "DLT pipeline scaffolding for cost centers",
         "task_title": "DLT pipeline — Cost Centers", "project_id": "prj-001",
         "created_by": "chris@example.com"},
        {"entry_id": "te-004", "task_id": "t-003", "user_id": "u-001",
         "hours": 5.0, "work_date": "2026-02-22", "notes": "SQL Server sync job configuration",
         "task_title": "SQL Server sync job", "project_id": "prj-001",
         "created_by": "cory@example.com"},
        {"entry_id": "te-005", "task_id": "t-003", "user_id": "u-001",
         "hours": 2.5, "work_date": "2026-02-23", "notes": "Debugging sync failures",
         "task_title": "SQL Server sync job", "project_id": "prj-001",
         "created_by": "cory@example.com"},
        {"entry_id": "te-006", "task_id": "t-004", "user_id": "u-002",
         "hours": 4.0, "work_date": "2026-02-24", "notes": "UAT comparison notebook draft",
         "task_title": "UAT comparison notebook", "project_id": "prj-001",
         "created_by": "chris@example.com"},
        {"entry_id": "te-007", "task_id": "t-007", "user_id": "u-003",
         "hours": 6.5, "work_date": "2026-02-24", "notes": "Balance sheet DLT pipeline build",
         "task_title": "Balance Sheet DLT", "project_id": "prj-001",
         "created_by": "anna@example.com"},
        {"entry_id": "te-008", "task_id": "t-008", "user_id": "u-001",
         "hours": 2.0, "work_date": "2026-02-25", "notes": "Finance access policy configuration",
         "task_title": "Access policy — Finance", "project_id": "prj-001",
         "created_by": "cory@example.com"},
        {"entry_id": "te-009", "task_id": "t-005", "user_id": "u-001",
         "hours": 3.0, "work_date": "2026-02-25", "notes": "GL mapping research and design",
         "task_title": "Bronze→Silver GL mapping", "project_id": "prj-001",
         "created_by": "cory@example.com"},
        {"entry_id": "te-010", "task_id": "t-002", "user_id": "u-002",
         "hours": 5.0, "work_date": "2026-02-25", "notes": "Cost center DLT pipeline testing",
         "task_title": "DLT pipeline — Cost Centers", "project_id": "prj-001",
         "created_by": "chris@example.com"},
    ])


# ---------------------------------------------------------------------------
# Public getters — route through mutable store
# ---------------------------------------------------------------------------

def get_departments() -> pd.DataFrame:
    """Return departments from mutable store."""
    return _get_store("departments", _init_departments).copy()


def get_portfolios() -> pd.DataFrame:
    """Return portfolios from mutable store."""
    return _get_store("portfolios", _init_portfolios).copy()


def get_portfolio_projects() -> pd.DataFrame:
    """Return portfolio projects from mutable store."""
    return _get_store("portfolio_projects", _init_portfolio_projects).copy()


def get_project_charter() -> pd.DataFrame:
    """Return project charter from mutable store."""
    return _get_store("project_charters", _init_project_charter).copy()


def get_sprints() -> pd.DataFrame:
    """Return sprints from mutable store."""
    return _get_store("sprints", _init_sprints).copy()


def get_tasks() -> pd.DataFrame:
    """Return tasks from mutable store."""
    return _get_store("tasks", _init_tasks).copy()


def get_risks() -> pd.DataFrame:
    """Return risks from mutable store."""
    return _get_store("risks", _init_risks).copy()


def get_resource_allocations() -> pd.DataFrame:
    """Return resource allocations from mutable store."""
    return _get_store("resource_allocations", _init_resource_allocations).copy()


def get_project_detail() -> pd.DataFrame:
    """Return project detail from mutable store."""
    return _get_store("projects", _init_project_detail).copy()


def get_project_phases() -> pd.DataFrame:
    """Return project phases from mutable store."""
    return _get_store("phases", _init_project_phases).copy()


def get_velocity() -> pd.DataFrame:
    """Return velocity data from mutable store."""
    return _get_store("velocity", _init_velocity).copy()


def get_burndown() -> pd.DataFrame:
    """Return burndown data from mutable store."""
    return _get_store("burndown", _init_burndown).copy()


def get_gate_status() -> pd.DataFrame:
    """Return gate status from mutable store."""
    return _get_store("gates", _init_gate_status).copy()


def get_cycle_times() -> pd.DataFrame:
    """Return cycle times from mutable store."""
    return _get_store("cycle_times", _init_cycle_times).copy()


def get_retro_items() -> pd.DataFrame:
    """Return retro items from mutable store."""
    return _get_store("retro_items", _init_retro_items).copy()


def get_audit_log() -> pd.DataFrame:
    """Return audit log from mutable store."""
    return _get_store("audit_log", _init_audit_log).copy()


def get_deliverables() -> pd.DataFrame:
    """Return deliverables from mutable store."""
    return _get_store("deliverables", _init_deliverables).copy()


def get_dependencies() -> pd.DataFrame:
    """Return dependencies from mutable store."""
    return _get_store("dependencies", _init_dependencies).copy()


def get_comments() -> pd.DataFrame:
    """Return comments from mutable store."""
    return _get_store("comments", _init_comments).copy()


def get_time_entries() -> pd.DataFrame:
    """Return time entries from mutable store."""
    return _get_store("time_entries", _init_time_entries).copy()


def get_team_members() -> pd.DataFrame:
    """Return team members from mutable store."""
    return _get_store("team_members", _init_team_members).copy()


def get_project_team() -> pd.DataFrame:
    """Return project team assignments from mutable store."""
    return _get_store("project_team", _init_project_team).copy()


def get_notifications() -> pd.DataFrame:
    """Return notifications from mutable store."""
    return _get_store("notifications", _seed_notifications).copy()


def _get_table_initializer(table_name: str) -> Optional[Callable[[], pd.DataFrame]]:
    """Return the initializer function for a given table, or None."""
    _initializers = {
        "departments": _init_departments, "portfolios": _init_portfolios,
        "portfolio_projects": _init_portfolio_projects,
        "project_charters": _init_project_charter, "sprints": _init_sprints,
        "tasks": _init_tasks, "risks": _init_risks,
        "resource_allocations": _init_resource_allocations,
        "projects": _init_project_detail, "phases": _init_project_phases,
        "velocity": _init_velocity, "burndown": _init_burndown,
        "gates": _init_gate_status, "cycle_times": _init_cycle_times,
        "retro_items": _init_retro_items, "audit_log": _init_audit_log,
        "deliverables": _init_deliverables, "dependencies": _init_dependencies,
        "comments": _init_comments, "time_entries": _init_time_entries,
        "team_members": _init_team_members, "project_team": _init_project_team,
        "notifications": _seed_notifications,
    }
    return _initializers.get(table_name)


def _seed_notifications():
    return pd.DataFrame([
        {"notification_id": "notif-001", "user_email": "alice@company.com",
         "notification_type": "task_assignment", "title": "Task Assigned",
         "message": "You've been assigned 'API Integration' task",
         "entity_type": "task", "entity_id": "t-001",
         "is_read": False, "created_at": "2026-02-25 10:00:00"},
        {"notification_id": "notif-002", "user_email": "alice@company.com",
         "notification_type": "charter_approved", "title": "Charter Approved",
         "message": "Data Pipeline Modernization charter has been approved",
         "entity_type": "charter", "entity_id": "ch-001",
         "is_read": True, "created_at": "2026-02-24 15:00:00"},
        {"notification_id": "notif-003", "user_email": "bob@company.com",
         "notification_type": "risk_escalation", "title": "Risk Escalated",
         "message": "High severity risk 'Data Quality' needs attention",
         "entity_type": "risk", "entity_id": "risk-001",
         "is_read": False, "created_at": "2026-02-25 14:00:00"},
        {"notification_id": "notif-004", "user_email": "alice@company.com",
         "notification_type": "sprint_closed", "title": "Sprint Closed",
         "message": "Sprint 'Sprint 4 — Integrations' has been closed",
         "entity_type": "sprint", "entity_id": "sp-004",
         "is_read": False, "created_at": "2026-02-26 09:00:00"},
        {"notification_id": "notif-005", "user_email": "carol@company.com",
         "notification_type": "gate_decision", "title": "Gate Decision",
         "message": "Design Review gate has been approved",
         "entity_type": "gate", "entity_id": "gate-002",
         "is_read": False, "created_at": "2026-02-26 11:00:00"},
    ])


def get_empty() -> pd.DataFrame:
    """Return an empty DataFrame."""
    return pd.DataFrame()
