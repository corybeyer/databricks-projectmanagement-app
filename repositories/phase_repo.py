"""Phase Repository — phase CRUD queries and operations."""

import pandas as pd
from repositories.base import query, write, safe_update, soft_delete
from models import sample_data


def get_phases(project_id: str, user_token: str = None) -> pd.DataFrame:
    """Get all non-deleted phases for a project, ordered by phase_order."""
    return query("""
        SELECT ph.*,
               COUNT(DISTINCT t.task_id) as task_count,
               COUNT(DISTINCT CASE WHEN t.status = 'done' THEN t.task_id END) as done_count
        FROM phases ph
        LEFT JOIN tasks t ON ph.phase_id = t.phase_id AND t.is_deleted = false
        WHERE ph.project_id = :project_id
          AND ph.is_deleted = false
        GROUP BY ALL
        ORDER BY ph.phase_order
    """, params={"project_id": project_id}, user_token=user_token,
        sample_fallback=sample_data.get_project_phases)


def get_phase_by_id(phase_id: str, user_token: str = None) -> pd.DataFrame:
    """Get a single phase by ID."""
    return query("""
        SELECT ph.*
        FROM phases ph
        WHERE ph.phase_id = :phase_id
          AND ph.is_deleted = false
    """, params={"phase_id": phase_id}, user_token=user_token,
        sample_fallback=sample_data.get_project_phases)


def create_phase(phase_data: dict, user_token: str = None) -> bool:
    """Insert a new phase record."""
    allowed_columns = {
        "phase_id", "project_id", "name", "phase_type", "phase_order",
        "delivery_method", "status", "start_date", "end_date",
        "actual_start", "actual_end", "pct_complete",
        "created_by",
    }
    params = {}
    used_cols = []
    for col in allowed_columns:
        if col in phase_data:
            if not col.isidentifier():
                raise ValueError(f"Invalid column name: {col!r}")
            used_cols.append(col)
            params[col] = phase_data[col]

    col_list = ", ".join(used_cols)
    param_list = ", ".join(f":{col}" for col in used_cols)
    return write(
        f"INSERT INTO phases ({col_list}) VALUES ({param_list})",
        params=params, user_token=user_token,
        table_name="phases", record=phase_data,
    )


def update_phase(phase_id: str, updates: dict, expected_updated_at: str,
                 user_email: str = None, user_token: str = None) -> bool:
    """Update a phase using optimistic locking."""
    return safe_update(
        "phases", "phase_id", phase_id, updates,
        expected_updated_at=expected_updated_at,
        user_email=user_email, user_token=user_token,
    )


def delete_phase(phase_id: str, user_email: str = None,
                 user_token: str = None) -> bool:
    """Soft-delete a phase."""
    return soft_delete(
        "phases", "phase_id", phase_id,
        user_email=user_email, user_token=user_token,
    )
