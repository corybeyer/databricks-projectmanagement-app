"""
Repository Base — Shared query infrastructure
===============================================
All domain repositories inherit query helpers from here.
Handles sample data fallback, optimistic locking, soft deletes.
"""

import logging
from typing import Optional
import pandas as pd
from db.unity_catalog import execute_query, execute_write

logger = logging.getLogger(__name__)

# Allowlists for dynamic SQL construction — defense-in-depth against injection.
# Only tables and columns listed here can be used in safe_update/soft_delete.
ALLOWED_TABLES = {
    "departments", "portfolios", "projects", "project_charters", "phases",
    "gates", "deliverables", "sprints", "tasks", "status_transitions",
    "comments", "time_entries", "team_members", "risks", "retro_items",
    "project_team", "dependencies", "audit_log", "notifications",
}

ALLOWED_ID_COLUMNS = {
    "department_id", "portfolio_id", "project_id", "charter_id", "phase_id",
    "gate_id", "deliverable_id", "sprint_id", "task_id", "transition_id",
    "comment_id", "entry_id", "user_id", "risk_id", "retro_id",
    "dependency_id", "audit_id", "notification_id",
}

# Per-table allowlists for mutable columns (used by safe_update).
# Excludes PKs, created_at, created_by, is_deleted, deleted_at, deleted_by.
ALLOWED_UPDATE_COLUMNS = {
    "departments": {
        "name", "description", "parent_dept_id", "head", "updated_by",
    },
    "portfolios": {
        "name", "description", "owner", "status", "health", "department_id",
        "budget_total", "strategic_priority", "updated_by",
    },
    "projects": {
        "name", "description", "owner", "sponsor", "status", "health",
        "delivery_method", "current_phase_id", "priority_rank", "pct_complete",
        "budget_total", "budget_spent", "start_date", "target_date",
        "actual_end_date", "portfolio_id", "updated_by",
    },
    "project_charters": {
        "project_name", "version", "business_case", "objectives",
        "scope_in", "scope_out", "assumptions", "constraints",
        "stakeholders", "success_criteria", "risks", "budget", "timeline",
        "delivery_method", "description", "approved_by", "approved_date",
        "updated_by",
    },
    "phases": {
        "name", "phase_type", "phase_order", "delivery_method", "status",
        "start_date", "end_date", "actual_start", "actual_end",
        "pct_complete", "updated_by",
    },
    "gates": {
        "gate_order", "name", "status", "criteria", "decision",
        "decided_by", "decided_at", "updated_by",
    },
    "deliverables": {
        "name", "description", "status", "owner", "due_date",
        "completed_date", "artifact_url", "updated_by",
    },
    "sprints": {
        "name", "goal", "start_date", "end_date", "status",
        "capacity_points", "phase_id", "updated_by",
    },
    "tasks": {
        "title", "description", "task_type", "status", "priority",
        "assignee", "story_points", "due_date", "backlog_rank",
        "sprint_id", "phase_id", "parent_task_id", "updated_by",
    },
    "comments": {
        "body", "updated_by",
    },
    "time_entries": {
        "task_id", "user_id", "hours", "work_date", "notes", "updated_by",
    },
    "team_members": {
        "display_name", "email", "department_id", "role", "is_active",
        "capacity_pct", "updated_by",
    },
    "project_team": {
        "project_role", "allocation_pct", "start_date", "end_date", "updated_by",
    },
    "risks": {
        "title", "description", "category", "probability", "impact",
        "risk_score", "status", "mitigation_plan", "response_strategy",
        "contingency_plan", "trigger_conditions", "risk_proximity",
        "risk_urgency", "residual_probability", "residual_impact",
        "residual_score", "secondary_risks", "identified_date",
        "last_review_date", "response_owner", "owner", "updated_by",
    },
    "retro_items": {
        "category", "body", "votes", "action_task_id", "updated_by",
    },
    "dependencies": {
        "dependency_type", "risk_level", "description", "status", "updated_by",
    },
    "notifications": {
        "is_read", "updated_by",
    },
}


def _use_sample_data() -> bool:
    """Check if we're in sample data mode."""
    from config import get_settings
    settings = get_settings()
    return settings.use_sample_data


def _validate_identifier(value: str, allowlist: set, label: str) -> None:
    """Validate that a SQL identifier is in the allowlist."""
    if value not in allowlist:
        raise ValueError(f"Invalid {label}: {value!r}")


def query(sql_str: str, params: dict = None, user_token: str = None,
          sample_fallback=None) -> pd.DataFrame:
    """Execute a read query with sample data fallback for local dev."""
    if _use_sample_data() and sample_fallback is not None:
        return sample_fallback()
    result = execute_query(sql_str, params=params, user_token=user_token)
    if result is None and sample_fallback is not None:
        return sample_fallback()
    return result if result is not None else pd.DataFrame()


def write(sql_str: str, params: dict = None, user_token: str = None,
          table_name: Optional[str] = None, record: Optional[dict] = None) -> bool:
    """Execute a write operation. In sample data mode, route to in-memory store."""
    if table_name:
        _validate_identifier(table_name, ALLOWED_TABLES, "table")
    if _use_sample_data() and table_name and record is not None:
        from models import sample_data
        sample_data.create_record(table_name, record)
        return True
    return execute_write(sql_str, params=params, user_token=user_token)


def safe_update(table: str, id_column: str, id_value: str,
                updates: dict, expected_updated_at: str,
                user_token: str = None, user_email: str = None) -> bool:
    """Optimistic locking update — fails if record was modified since last read."""
    _validate_identifier(table, ALLOWED_TABLES, "table")
    _validate_identifier(id_column, ALLOWED_ID_COLUMNS, "id_column")
    if table in ALLOWED_UPDATE_COLUMNS:
        for col in updates:
            if col not in ALLOWED_UPDATE_COLUMNS[table]:
                raise ValueError(f"Column {col!r} not allowed for update on table {table!r}")
    else:
        for col in updates:
            if not col.isidentifier():
                raise ValueError(f"Invalid column name: {col!r}")

    if _use_sample_data():
        from models import sample_data
        if user_email:
            updates = {**updates, "updated_by": user_email}
        return sample_data.update_record(
            table, id_column, id_value, updates,
            expected_updated_at=expected_updated_at,
        )

    if user_email:
        updates = {**updates, "updated_by": user_email}

    set_clauses = ", ".join(f"{col} = :{col}" for col in updates)
    if expected_updated_at is not None:
        sql_str = (
            f"UPDATE {table} SET {set_clauses}, updated_at = current_timestamp() "
            f"WHERE {id_column} = :_id AND updated_at = :_expected_updated_at"
        )
        params = {**updates, "_id": id_value, "_expected_updated_at": expected_updated_at}
    else:
        sql_str = (
            f"UPDATE {table} SET {set_clauses}, updated_at = current_timestamp() "
            f"WHERE {id_column} = :_id AND is_deleted = false"
        )
        params = {**updates, "_id": id_value}
    return write(sql_str, params=params, user_token=user_token)


def soft_delete(table: str, id_column: str, id_value: str,
                user_token: str = None, user_email: str = None) -> bool:
    """Soft delete — sets is_deleted = true and deleted_at = now()."""
    _validate_identifier(table, ALLOWED_TABLES, "table")
    _validate_identifier(id_column, ALLOWED_ID_COLUMNS, "id_column")

    if _use_sample_data():
        from models import sample_data
        return sample_data.delete_record(table, id_column, id_value, user_email=user_email)

    deleted_by_clause = ", deleted_by = :_email" if user_email else ""
    sql_str = (
        f"UPDATE {table} SET is_deleted = true, deleted_at = current_timestamp(), "
        f"updated_at = current_timestamp(){deleted_by_clause} "
        f"WHERE {id_column} = :_id AND is_deleted = false"
    )
    params = {"_id": id_value}
    if user_email:
        params["_email"] = user_email
    return write(sql_str, params=params, user_token=user_token)
