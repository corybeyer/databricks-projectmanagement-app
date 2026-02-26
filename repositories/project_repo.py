"""Project Repository — project detail and phase queries."""

import pandas as pd
from repositories.base import query
from models import sample_data


def get_project_detail(project_id: str, user_token: str = None) -> pd.DataFrame:
    return query("""
        SELECT pr.*,
               pf.name as portfolio_name,
               ph.name as current_phase_name,
               ph.delivery_method
        FROM projects pr
        LEFT JOIN portfolios pf ON pr.portfolio_id = pf.portfolio_id
        LEFT JOIN phases ph ON pr.current_phase_id = ph.phase_id
        WHERE pr.project_id = :project_id
    """, params={"project_id": project_id}, user_token=user_token,
        sample_fallback=sample_data.get_empty)


def get_project_phases(project_id: str, user_token: str = None) -> pd.DataFrame:
    return query("""
        SELECT ph.*,
               COUNT(DISTINCT t.task_id) as task_count,
               COUNT(DISTINCT CASE WHEN t.status = 'done' THEN t.task_id END) as done_count
        FROM phases ph
        LEFT JOIN tasks t ON ph.phase_id = t.phase_id
        WHERE ph.project_id = :project_id
        GROUP BY ALL
        ORDER BY ph.phase_order
    """, params={"project_id": project_id}, user_token=user_token,
        sample_fallback=sample_data.get_empty)
