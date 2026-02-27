"""Dependency Repository — cross-project dependency queries and CRUD."""

import pandas as pd
from repositories.base import query, write, safe_update, soft_delete
from models import sample_data


def get_dependencies(project_id: str = None, user_token: str = None) -> pd.DataFrame:
    """Get all dependencies, optionally filtered to those involving a project."""
    if project_id:
        return query("""
            SELECT d.*,
                   sp.name as source_project_name,
                   tp.name as target_project_name
            FROM dependencies d
            LEFT JOIN projects sp ON d.source_project_id = sp.project_id
            LEFT JOIN projects tp ON d.target_project_id = tp.project_id
            WHERE d.is_deleted = false
              AND (d.source_project_id = :project_id
                   OR d.target_project_id = :project_id)
            ORDER BY d.created_at DESC
        """, params={"project_id": project_id}, user_token=user_token,
            sample_fallback=sample_data.get_dependencies)

    return query("""
        SELECT d.*,
               sp.name as source_project_name,
               tp.name as target_project_name
        FROM dependencies d
        LEFT JOIN projects sp ON d.source_project_id = sp.project_id
        LEFT JOIN projects tp ON d.target_project_id = tp.project_id
        WHERE d.is_deleted = false
        ORDER BY d.created_at DESC
    """, user_token=user_token, sample_fallback=sample_data.get_dependencies)


def get_dependency_by_id(dependency_id: str, user_token: str = None) -> pd.DataFrame:
    """Get a single dependency by ID."""
    return query("""
        SELECT d.*,
               sp.name as source_project_name,
               tp.name as target_project_name
        FROM dependencies d
        LEFT JOIN projects sp ON d.source_project_id = sp.project_id
        LEFT JOIN projects tp ON d.target_project_id = tp.project_id
        WHERE d.dependency_id = :dependency_id
          AND d.is_deleted = false
    """, params={"dependency_id": dependency_id}, user_token=user_token,
        sample_fallback=sample_data.get_dependencies)


def create_dependency(dep_data: dict, user_token: str = None) -> bool:
    """Insert a new dependency record."""
    allowed_columns = {
        "dependency_id", "source_project_id", "source_task_id",
        "target_project_id", "target_task_id", "dependency_type",
        "risk_level", "description", "status",
        "created_by",
    }
    params = {}
    used_cols = []
    for col in allowed_columns:
        if col in dep_data:
            if not col.isidentifier():
                raise ValueError(f"Invalid column name: {col!r}")
            used_cols.append(col)
            params[col] = dep_data[col]

    col_list = ", ".join(used_cols)
    param_list = ", ".join(f":{col}" for col in used_cols)
    return write(
        f"INSERT INTO dependencies ({col_list}) VALUES ({param_list})",
        params=params, user_token=user_token,
        table_name="dependencies", record=dep_data,
    )


def update_dependency(dependency_id: str, updates: dict, expected_updated_at: str,
                      user_email: str = None, user_token: str = None) -> bool:
    """Update a dependency using optimistic locking."""
    return safe_update(
        "dependencies", "dependency_id", dependency_id, updates,
        expected_updated_at=expected_updated_at,
        user_email=user_email, user_token=user_token,
    )


def delete_dependency(dependency_id: str, user_email: str = None,
                      user_token: str = None) -> bool:
    """Soft-delete a dependency."""
    return soft_delete(
        "dependencies", "dependency_id", dependency_id,
        user_email=user_email, user_token=user_token,
    )


def resolve_dependency(dependency_id: str, user_email: str = None,
                       user_token: str = None) -> bool:
    """Set dependency status to resolved via safe_update."""
    return safe_update(
        "dependencies", "dependency_id", dependency_id,
        {"status": "resolved"},
        expected_updated_at=None,
        user_email=user_email, user_token=user_token,
    )
