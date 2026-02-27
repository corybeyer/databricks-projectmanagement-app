"""Time Entry Repository — time tracking queries and CRUD."""

import pandas as pd
from repositories.base import query, write, safe_update, soft_delete
from models import sample_data


def get_time_entries(project_id: str = None, user_token: str = None) -> pd.DataFrame:
    """Get all time entries for a project, joined with task title."""
    if project_id:
        return query("""
            SELECT te.*,
                   t.title as task_title,
                   t.project_id
            FROM time_entries te
            LEFT JOIN tasks t ON te.task_id = t.task_id
            WHERE te.is_deleted = false
              AND t.project_id = :project_id
            ORDER BY te.work_date DESC, te.created_at DESC
        """, params={"project_id": project_id}, user_token=user_token,
            sample_fallback=sample_data.get_time_entries)

    return query("""
        SELECT te.*,
               t.title as task_title,
               t.project_id
        FROM time_entries te
        LEFT JOIN tasks t ON te.task_id = t.task_id
        WHERE te.is_deleted = false
        ORDER BY te.work_date DESC, te.created_at DESC
    """, user_token=user_token, sample_fallback=sample_data.get_time_entries)


def get_time_entries_by_task(task_id: str, user_token: str = None) -> pd.DataFrame:
    """Get all time entries for a specific task."""
    return query("""
        SELECT te.*,
               t.title as task_title,
               t.project_id
        FROM time_entries te
        LEFT JOIN tasks t ON te.task_id = t.task_id
        WHERE te.task_id = :task_id
          AND te.is_deleted = false
        ORDER BY te.work_date DESC
    """, params={"task_id": task_id}, user_token=user_token,
        sample_fallback=sample_data.get_time_entries)


def get_time_entries_by_user(user_id: str, user_token: str = None) -> pd.DataFrame:
    """Get all time entries for a specific user."""
    return query("""
        SELECT te.*,
               t.title as task_title,
               t.project_id
        FROM time_entries te
        LEFT JOIN tasks t ON te.task_id = t.task_id
        WHERE te.user_id = :user_id
          AND te.is_deleted = false
        ORDER BY te.work_date DESC
    """, params={"user_id": user_id}, user_token=user_token,
        sample_fallback=sample_data.get_time_entries)


def get_time_entry_by_id(entry_id: str, user_token: str = None) -> pd.DataFrame:
    """Get a single time entry by ID."""
    return query("""
        SELECT te.*,
               t.title as task_title,
               t.project_id
        FROM time_entries te
        LEFT JOIN tasks t ON te.task_id = t.task_id
        WHERE te.entry_id = :entry_id
          AND te.is_deleted = false
    """, params={"entry_id": entry_id}, user_token=user_token,
        sample_fallback=sample_data.get_time_entries)


def create_time_entry(data: dict, user_token: str = None) -> bool:
    """Insert a new time entry record."""
    allowed_columns = {
        "entry_id", "task_id", "user_id", "hours", "work_date",
        "notes", "created_by", "updated_by",
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
        f"INSERT INTO time_entries ({col_list}) VALUES ({param_list})",
        params=params, user_token=user_token,
        table_name="time_entries", record=data,
    )


def update_time_entry(entry_id: str, updates: dict, expected_updated_at: str,
                      user_email: str = None, user_token: str = None) -> bool:
    """Update a time entry using optimistic locking."""
    return safe_update(
        "time_entries", "entry_id", entry_id, updates,
        expected_updated_at=expected_updated_at,
        user_email=user_email, user_token=user_token,
    )


def delete_time_entry(entry_id: str, user_email: str = None,
                      user_token: str = None) -> bool:
    """Soft-delete a time entry."""
    return soft_delete(
        "time_entries", "entry_id", entry_id,
        user_email=user_email, user_token=user_token,
    )


def get_time_summary_by_task(project_id: str, user_token: str = None) -> pd.DataFrame:
    """Get aggregated hours per task for a project."""
    return query("""
        SELECT t.task_id,
               t.title as task_title,
               COALESCE(SUM(te.hours), 0) as total_hours,
               COUNT(te.entry_id) as entry_count
        FROM tasks t
        LEFT JOIN time_entries te ON t.task_id = te.task_id AND te.is_deleted = false
        WHERE t.project_id = :project_id
          AND t.is_deleted = false
        GROUP BY t.task_id, t.title
        HAVING COALESCE(SUM(te.hours), 0) > 0
        ORDER BY total_hours DESC
    """, params={"project_id": project_id}, user_token=user_token,
        sample_fallback=sample_data.get_time_entries)
