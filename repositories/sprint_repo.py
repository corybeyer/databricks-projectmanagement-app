"""Sprint Repository — sprint and sprint task queries."""

import pandas as pd
from repositories.base import query
from models import sample_data


def get_sprints(project_id: str, user_token: str = None) -> pd.DataFrame:
    return query("""
        SELECT s.*,
               SUM(t.story_points) as total_points,
               SUM(CASE WHEN t.status = 'done' THEN t.story_points ELSE 0 END) as done_points
        FROM sprints s
        LEFT JOIN tasks t ON s.sprint_id = t.sprint_id
        WHERE s.project_id = :project_id
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
        ORDER BY t.backlog_rank
    """, params={"sprint_id": sprint_id}, user_token=user_token,
        sample_fallback=sample_data.get_tasks)
