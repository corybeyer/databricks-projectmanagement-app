"""Task Repository — task CRUD and status transitions."""

import pandas as pd
from repositories.base import query, write, safe_update, soft_delete
from models import sample_data


def get_all_tasks(user_token: str = None) -> pd.DataFrame:
    """Get all non-deleted tasks across all projects."""
    return query("""
        SELECT t.*,
               tm.display_name as assignee_name
        FROM tasks t
        LEFT JOIN team_members tm ON t.assignee = tm.user_id
        WHERE t.is_deleted = false
        ORDER BY t.status, t.title
    """, user_token=user_token, sample_fallback=sample_data.get_tasks)


def get_backlog(project_id: str, user_token: str = None) -> pd.DataFrame:
    return query("""
        SELECT t.*,
               tm.display_name as assignee_name
        FROM tasks t
        LEFT JOIN team_members tm ON t.assignee = tm.user_id
        WHERE t.project_id = :project_id
          AND t.sprint_id IS NULL
          AND t.is_deleted = false
        ORDER BY t.backlog_rank
    """, params={"project_id": project_id}, user_token=user_token,
        sample_fallback=sample_data.get_tasks)


def get_task_by_id(task_id: str, user_token: str = None) -> pd.DataFrame:
    return query(
        "SELECT * FROM tasks WHERE task_id = :task_id AND is_deleted = false",
        params={"task_id": task_id}, user_token=user_token,
        sample_fallback=sample_data.get_tasks,
    )


def create_task(task_data: dict, user_token: str = None) -> bool:
    allowed_columns = {"task_id", "title", "task_type", "status", "story_points",
                       "assignee", "project_id", "sprint_id", "phase_id",
                       "priority", "backlog_rank", "created_by", "description",
                       "due_date"}
    params = {}
    used_cols = []
    for col in allowed_columns:
        if col in task_data:
            if not col.isidentifier():
                raise ValueError(f"Invalid column name: {col!r}")
            used_cols.append(col)
            params[col] = task_data[col]

    col_list = ", ".join(used_cols)
    param_list = ", ".join(f":{col}" for col in used_cols)
    return write(
        f"INSERT INTO tasks ({col_list}) VALUES ({param_list})",
        params=params, user_token=user_token,
        table_name="tasks", record=task_data,
    )


def update_task(task_id: str, updates: dict, expected_updated_at: str,
                user_email: str = None, user_token: str = None) -> bool:
    return safe_update(
        "tasks", "task_id", task_id, updates,
        expected_updated_at=expected_updated_at,
        user_email=user_email, user_token=user_token,
    )


def delete_task(task_id: str, user_email: str = None,
                user_token: str = None) -> bool:
    return soft_delete(
        "tasks", "task_id", task_id,
        user_email=user_email, user_token=user_token,
    )


def update_task_status(task_id: str, new_status: str, changed_by: str,
                       user_token: str = None) -> bool:
    current = query(
        "SELECT status FROM tasks WHERE task_id = :task_id AND is_deleted = false",
        params={"task_id": task_id}, user_token=user_token,
        sample_fallback=sample_data.get_empty,
    )
    old_status = current.iloc[0]["status"] if len(current) > 0 else "unknown"

    success = safe_update(
        "tasks", "task_id", task_id,
        {"status": new_status},
        expected_updated_at=None,
        user_token=user_token,
    )

    if success:
        write("""
            INSERT INTO status_transitions
            (transition_id, task_id, from_status, to_status, changed_by, transitioned_at)
            VALUES (uuid(), :task_id, :old_status, :new_status, :changed_by, current_timestamp())
        """, params={
            "task_id": task_id, "old_status": old_status,
            "new_status": new_status, "changed_by": changed_by,
        }, user_token=user_token)

    return success


def move_task_to_sprint(task_id: str, sprint_id: str, user_token: str = None) -> bool:
    return safe_update(
        "tasks", "task_id", task_id,
        {"sprint_id": sprint_id},
        expected_updated_at=None,
        user_token=user_token,
    )
