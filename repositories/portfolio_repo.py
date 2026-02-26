"""Portfolio Repository — portfolio and portfolio-project queries."""

import pandas as pd
from repositories.base import query
from models import sample_data


def get_portfolios(user_token: str = None) -> pd.DataFrame:
    return query("""
        SELECT p.*,
               COUNT(DISTINCT pr.project_id) as project_count,
               AVG(pr.pct_complete) as avg_completion,
               SUM(pr.budget_spent) as total_spent,
               SUM(pr.budget_total) as total_budget
        FROM portfolios p
        LEFT JOIN projects pr ON p.portfolio_id = pr.portfolio_id
        GROUP BY ALL
        ORDER BY p.name
    """, user_token=user_token, sample_fallback=sample_data.get_portfolios)


def get_portfolio_projects(portfolio_id: str, user_token: str = None) -> pd.DataFrame:
    return query("""
        SELECT pr.*,
               ph.name as current_phase_name,
               ph.phase_type,
               s.name as active_sprint_name,
               s.sprint_id as active_sprint_id
        FROM projects pr
        LEFT JOIN phases ph ON pr.current_phase_id = ph.phase_id
        LEFT JOIN sprints s ON pr.project_id = s.project_id AND s.status = 'active'
        WHERE pr.portfolio_id = :portfolio_id
        ORDER BY pr.priority_rank
    """, params={"portfolio_id": portfolio_id}, user_token=user_token,
        sample_fallback=sample_data.get_portfolio_projects)
