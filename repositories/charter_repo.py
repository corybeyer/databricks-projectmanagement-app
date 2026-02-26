"""Charter Repository — project charter CRUD operations."""

import pandas as pd
from repositories.base import query, write, safe_update, soft_delete
from models import sample_data


def get_charters(project_id: str, user_token: str = None) -> pd.DataFrame:
    """Get all non-deleted charters for a project."""
    return query("""
        SELECT c.*
        FROM project_charters c
        WHERE c.project_id = :project_id
          AND c.is_deleted = false
        ORDER BY c.created_at DESC
    """, params={"project_id": project_id}, user_token=user_token,
        sample_fallback=sample_data.get_project_charter)


def get_charter_by_id(charter_id: str, user_token: str = None) -> pd.DataFrame:
    """Get a single charter by ID."""
    return query(
        "SELECT * FROM project_charters WHERE charter_id = :charter_id AND is_deleted = false",
        params={"charter_id": charter_id}, user_token=user_token,
        sample_fallback=sample_data.get_project_charter,
    )


def get_project_charter(project_id: str, user_token: str = None) -> pd.DataFrame:
    """Legacy function — get the charter for a project (backward compat)."""
    return get_charters(project_id, user_token=user_token)


def create_charter(charter_data: dict, user_token: str = None) -> bool:
    """Insert a new charter. Uses allowed_columns whitelist."""
    allowed_columns = {
        "charter_id", "project_id", "project_name", "description",
        "business_case", "objectives", "scope_in", "scope_out",
        "stakeholders", "success_criteria", "risks", "budget", "timeline",
        "delivery_method", "status", "version",
        "approved_by", "approved_date",
        "created_by", "updated_by",
    }
    params = {}
    used_cols = []
    for col in allowed_columns:
        if col in charter_data:
            if not col.isidentifier():
                raise ValueError(f"Invalid column name: {col!r}")
            used_cols.append(col)
            params[col] = charter_data[col]

    col_list = ", ".join(used_cols)
    param_list = ", ".join(f":{col}" for col in used_cols)
    return write(
        f"INSERT INTO project_charters ({col_list}) VALUES ({param_list})",
        params=params, user_token=user_token,
        table_name="project_charters", record=charter_data,
    )


def update_charter(charter_id: str, updates: dict, expected_updated_at: str,
                    user_email: str = None, user_token: str = None) -> bool:
    """Update a charter via optimistic locking."""
    return safe_update(
        "project_charters", "charter_id", charter_id, updates,
        expected_updated_at=expected_updated_at,
        user_email=user_email, user_token=user_token,
    )


def delete_charter(charter_id: str, user_email: str = None,
                    user_token: str = None) -> bool:
    """Soft-delete a charter."""
    return soft_delete(
        "project_charters", "charter_id", charter_id,
        user_email=user_email, user_token=user_token,
    )


def update_charter_status(charter_id: str, new_status: str,
                           user_email: str = None,
                           user_token: str = None) -> bool:
    """Update a charter's status field."""
    return safe_update(
        "project_charters", "charter_id", charter_id,
        {"status": new_status},
        expected_updated_at=None,
        user_email=user_email, user_token=user_token,
    )
