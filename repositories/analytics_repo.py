"""Analytics Repository — velocity, burndown, cycle times, gates."""

import pandas as pd
from repositories.base import query
from models import sample_data


def get_velocity(project_id: str, user_token: str = None) -> pd.DataFrame:
    return query("""
        SELECT s.name as sprint_name,
               s.start_date,
               s.end_date,
               SUM(CASE WHEN t.status = 'done' THEN t.story_points ELSE 0 END) as completed_points,
               SUM(t.story_points) as committed_points,
               s.capacity_points
        FROM sprints s
        LEFT JOIN tasks t ON s.sprint_id = t.sprint_id
        WHERE s.project_id = :project_id
          AND s.status = 'closed'
          AND s.is_deleted = false
        GROUP BY ALL
        ORDER BY s.start_date
    """, params={"project_id": project_id}, user_token=user_token,
        sample_fallback=sample_data.get_empty)


def get_burndown(sprint_id: str, user_token: str = None) -> pd.DataFrame:
    return query("""
        WITH sprint_info AS (
            SELECT start_date, end_date
            FROM sprints WHERE sprint_id = :sprint_id
        ),
        date_series AS (
            SELECT explode(sequence(
                (SELECT start_date FROM sprint_info),
                (SELECT end_date FROM sprint_info),
                interval 1 day
            )) as burn_date
        )
        SELECT d.burn_date,
               SUM(CASE WHEN t.status != 'done' THEN t.story_points ELSE 0 END) as remaining_points,
               SUM(t.story_points) as total_points
        FROM date_series d
        CROSS JOIN tasks t TIMESTAMP AS OF d.burn_date
        WHERE t.sprint_id = :sprint_id
          AND t.is_deleted = false
        GROUP BY d.burn_date
        ORDER BY d.burn_date
    """, params={"sprint_id": sprint_id}, user_token=user_token,
        sample_fallback=sample_data.get_empty)


def get_status_cycle_times(project_id: str, user_token: str = None) -> pd.DataFrame:
    return query("""
        SELECT t.task_id, t.title, t.task_type,
               st.from_status, st.to_status,
               st.transitioned_at,
               LEAD(st.transitioned_at) OVER (
                   PARTITION BY t.task_id ORDER BY st.transitioned_at
               ) as next_transition,
               TIMESTAMPDIFF(HOUR,
                   st.transitioned_at,
                   LEAD(st.transitioned_at) OVER (
                       PARTITION BY t.task_id ORDER BY st.transitioned_at
                   )
               ) as hours_in_status
        FROM status_transitions st
        JOIN tasks t ON st.task_id = t.task_id
        WHERE t.project_id = :project_id
          AND t.is_deleted = false
        ORDER BY t.task_id, st.transitioned_at
    """, params={"project_id": project_id}, user_token=user_token,
        sample_fallback=sample_data.get_empty)


def get_gate_status(project_id: str, user_token: str = None) -> pd.DataFrame:
    return query("""
        SELECT g.*,
               ph.name as phase_name
        FROM gates g
        JOIN phases ph ON g.phase_id = ph.phase_id
        WHERE ph.project_id = :project_id
          AND g.is_deleted = false
        ORDER BY g.gate_order
    """, params={"project_id": project_id}, user_token=user_token,
        sample_fallback=sample_data.get_empty)
