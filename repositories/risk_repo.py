"""Risk Repository — risk register queries."""

import pandas as pd
from repositories.base import query
from models import sample_data


def get_risks(portfolio_id: str = None, user_token: str = None) -> pd.DataFrame:
    if portfolio_id:
        return query("""
            SELECT r.*,
                   pr.name as project_name,
                   pf.name as portfolio_name
            FROM risks r
            LEFT JOIN projects pr ON r.project_id = pr.project_id
            LEFT JOIN portfolios pf ON r.portfolio_id = pf.portfolio_id
            WHERE r.is_deleted = false
              AND r.portfolio_id = :portfolio_id
            ORDER BY r.risk_score DESC
        """, params={"portfolio_id": portfolio_id}, user_token=user_token,
            sample_fallback=sample_data.get_risks)

    return query("""
        SELECT r.*,
               pr.name as project_name,
               pf.name as portfolio_name
        FROM risks r
        LEFT JOIN projects pr ON r.project_id = pr.project_id
        LEFT JOIN portfolios pf ON r.portfolio_id = pf.portfolio_id
        WHERE r.is_deleted = false
        ORDER BY r.risk_score DESC
    """, user_token=user_token, sample_fallback=sample_data.get_risks)
