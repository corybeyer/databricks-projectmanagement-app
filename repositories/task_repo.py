"""Task Repository — task CRUD and status transitions."""

import pandas as pd
from repositories.base import query, write
from models import sample_data


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


def create_task(task_data: dict, user_token: str = None) -> bool:
    columns = ["task_id", "title", "task_type", "status", "story_points",
               "assignee", "project_id", "sprint_id", "phase_id",
               "priority", "backlog_rank"]
    params = {}
    used_cols = []
    for col in columns:
        if col in task_data:
            used_cols.append(col)
            params[col] = task_data[col]

    col_list = ", ".join(used_cols)
    param_list = ", ".join(f":{col}" for col in used_cols)
    return write(
        f"INSERT INTO tasks ({col_list}) VALUES ({param_list})",
        params=params, user_token=user_token,
    )


def update_task_status(task_id: str, new_status: str, changed_by: str,
                       user_token: str = None) -> bool:
    current = query(
        "SELECT status FROM tasks WHERE task_id = :task_id AND is_deleted = false",
        params={"task_id": task_id}, user_token=user_token,
        sample_fallback=sample_data.get_empty,
    )
    old_status = current.iloc[0]["status"] if len(current) > 0 else "unknown"

    success = write("""
        UPDATE tasks
        SET status = :new_status, updated_at = current_timestamp()
        WHERE task_id = :task_id
    """, params={"task_id": task_id, "new_status": new_status}, user_token=user_token)

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
    return write(
        "UPDATE tasks SET sprint_id = :sprint_id WHERE task_id = :task_id",
        params={"task_id": task_id, "sprint_id": sprint_id}, user_token=user_token,
    )
