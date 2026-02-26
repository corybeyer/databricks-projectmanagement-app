"""Resource Repository — team allocations and retro items."""

import pandas as pd
from repositories.base import query
from models import sample_data


def get_resource_allocations(user_token: str = None) -> pd.DataFrame:
    return query("""
        SELECT tm.user_id, tm.display_name, tm.role,
               pr.name as project_name,
               pr.project_id,
               COUNT(DISTINCT t.task_id) as task_count,
               SUM(t.story_points) as points_assigned,
               SUM(CASE WHEN t.status = 'done' THEN t.story_points ELSE 0 END) as points_done
        FROM team_members tm
        LEFT JOIN tasks t ON tm.user_id = t.assignee AND t.status != 'done' AND t.is_deleted = false
        LEFT JOIN projects pr ON t.project_id = pr.project_id
        WHERE tm.is_active = true
        GROUP BY ALL
        ORDER BY tm.display_name, pr.name
    """, user_token=user_token, sample_fallback=sample_data.get_resource_allocations)


def get_retro_items(sprint_id: str, user_token: str = None) -> pd.DataFrame:
    return query("""
        SELECT ri.*
        FROM retro_items ri
        WHERE ri.sprint_id = :sprint_id
          AND ri.is_deleted = false
        ORDER BY ri.votes DESC
    """, params={"sprint_id": sprint_id}, user_token=user_token,
        sample_fallback=sample_data.get_empty)
