"""Deliverable Repository — deliverable tracking queries and CRUD."""

import pandas as pd
from repositories.base import query, write, safe_update, soft_delete
from models import sample_data


def get_deliverables(phase_id: str = None, user_token: str = None) -> pd.DataFrame:
    """Get all deliverables, optionally filtered by phase."""
    if phase_id:
        return query("""
            SELECT d.*,
                   p.name as phase_name,
                   p.phase_type
            FROM deliverables d
            LEFT JOIN phases p ON d.phase_id = p.phase_id
            WHERE d.is_deleted = false
              AND d.phase_id = :phase_id
            ORDER BY d.due_date ASC
        """, params={"phase_id": phase_id}, user_token=user_token,
            sample_fallback=sample_data.get_deliverables)

    return query("""
        SELECT d.*,
               p.name as phase_name,
               p.phase_type
        FROM deliverables d
        LEFT JOIN phases p ON d.phase_id = p.phase_id
        WHERE d.is_deleted = false
        ORDER BY d.due_date ASC
    """, user_token=user_token, sample_fallback=sample_data.get_deliverables)


def get_deliverables_by_project(project_id: str, user_token: str = None) -> pd.DataFrame:
    """Get all deliverables across all phases of a project."""
    return query("""
        SELECT d.*,
               p.name as phase_name,
               p.phase_type
        FROM deliverables d
        JOIN phases p ON d.phase_id = p.phase_id
        WHERE p.project_id = :project_id
          AND d.is_deleted = false
        ORDER BY p.phase_order ASC, d.due_date ASC
    """, params={"project_id": project_id}, user_token=user_token,
        sample_fallback=sample_data.get_deliverables)


def get_deliverable_by_id(deliverable_id: str, user_token: str = None) -> pd.DataFrame:
    """Get a single deliverable by ID."""
    return query("""
        SELECT d.*,
               p.name as phase_name,
               p.phase_type
        FROM deliverables d
        LEFT JOIN phases p ON d.phase_id = p.phase_id
        WHERE d.deliverable_id = :deliverable_id
          AND d.is_deleted = false
    """, params={"deliverable_id": deliverable_id}, user_token=user_token,
        sample_fallback=sample_data.get_deliverables)


def create_deliverable(data: dict, user_token: str = None) -> bool:
    """Insert a new deliverable record."""
    allowed_columns = {
        "deliverable_id", "phase_id", "name", "description",
        "status", "owner", "due_date", "completed_date",
        "artifact_url", "created_by",
    }
    params = {}
    used_cols = []
    for col in allowed_columns:
        if col in data:
            if not col.isidentifier():
                raise ValueError(f"Invalid column name: {col!r}")
            used_cols.append(col)
            params[col] = data[col]

    col_list = ", ".join(used_cols)
    param_list = ", ".join(f":{col}" for col in used_cols)
    return write(
        f"INSERT INTO deliverables ({col_list}) VALUES ({param_list})",
        params=params, user_token=user_token,
        table_name="deliverables", record=data,
    )


def update_deliverable(deliverable_id: str, updates: dict,
                       expected_updated_at: str,
                       user_email: str = None,
                       user_token: str = None) -> bool:
    """Update a deliverable using optimistic locking."""
    return safe_update(
        "deliverables", "deliverable_id", deliverable_id, updates,
        expected_updated_at=expected_updated_at,
        user_email=user_email, user_token=user_token,
    )


def delete_deliverable(deliverable_id: str, user_email: str = None,
                       user_token: str = None) -> bool:
    """Soft-delete a deliverable."""
    return soft_delete(
        "deliverables", "deliverable_id", deliverable_id,
        user_email=user_email, user_token=user_token,
    )


def update_deliverable_status(deliverable_id: str, new_status: str,
                              user_email: str = None,
                              user_token: str = None) -> bool:
    """Update deliverable status via safe_update."""
    return safe_update(
        "deliverables", "deliverable_id", deliverable_id,
        {"status": new_status},
        expected_updated_at=None,
        user_email=user_email, user_token=user_token,
    )
