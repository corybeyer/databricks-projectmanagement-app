"""Sprint Repository — sprint and sprint task queries."""

import pandas as pd
from repositories.base import query, write, safe_update, soft_delete
from models import sample_data


def get_sprints(project_id: str, user_token: str = None) -> pd.DataFrame:
    return query("""
        SELECT s.*,
               SUM(t.story_points) as total_points,
               SUM(CASE WHEN t.status = 'done' THEN t.story_points ELSE 0 END) as done_points
        FROM sprints s
        LEFT JOIN tasks t ON s.sprint_id = t.sprint_id
        WHERE s.project_id = :project_id
          AND s.is_deleted = false
        GROUP BY ALL
        ORDER BY s.start_date
    """, params={"project_id": project_id}, user_token=user_token,
        sample_fallback=sample_data.get_sprints)


def get_sprint_tasks(sprint_id: str, user_token: str = None) -> pd.DataFrame:
    return query("""
        SELECT t.*,
               tm.display_name as assignee_name
        FROM tasks t
        LEFT JOIN team_members tm ON t.assignee = tm.user_id
        WHERE t.sprint_id = :sprint_id
          AND t.is_deleted = false
        ORDER BY t.backlog_rank
    """, params={"sprint_id": sprint_id}, user_token=user_token,
        sample_fallback=sample_data.get_tasks)


def get_sprint_by_id(sprint_id: str, user_token: str = None) -> pd.DataFrame:
    return query(
        "SELECT * FROM sprints WHERE sprint_id = :sprint_id AND is_deleted = false",
        params={"sprint_id": sprint_id}, user_token=user_token,
        sample_fallback=sample_data.get_sprints,
    )


def create_sprint(sprint_data: dict, user_token: str = None) -> bool:
    allowed_columns = {"sprint_id", "name", "project_id", "phase_id", "status",
                       "start_date", "end_date", "capacity_points", "goal",
                       "created_by"}
    params = {}
    used_cols = []
    for col in allowed_columns:
        if col in sprint_data:
            if not col.isidentifier():
                raise ValueError(f"Invalid column name: {col!r}")
            used_cols.append(col)
            params[col] = sprint_data[col]

    col_list = ", ".join(used_cols)
    param_list = ", ".join(f":{col}" for col in used_cols)
    return write(
        f"INSERT INTO sprints ({col_list}) VALUES ({param_list})",
        params=params, user_token=user_token,
        table_name="sprints", record=sprint_data,
    )


def update_sprint(sprint_id: str, updates: dict, expected_updated_at: str,
                  user_email: str = None, user_token: str = None) -> bool:
    return safe_update(
        "sprints", "sprint_id", sprint_id, updates,
        expected_updated_at=expected_updated_at,
        user_email=user_email, user_token=user_token,
    )


def close_sprint(sprint_id: str, user_email: str = None,
                 user_token: str = None) -> bool:
    return safe_update(
        "sprints", "sprint_id", sprint_id,
        {"status": "closed"},
        expected_updated_at=None,
        user_email=user_email, user_token=user_token,
    )
