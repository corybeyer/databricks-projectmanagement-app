"""Risk Repository — risk register queries."""

import pandas as pd
from repositories.base import query
from models import sample_data


def get_risks(portfolio_id: str = None, user_token: str = None) -> pd.DataFrame:
    params = {}
    conditions = ["r.is_deleted = false"]
    if portfolio_id:
        conditions.append("r.portfolio_id = :portfolio_id")
        params["portfolio_id"] = portfolio_id

    where = f"WHERE {' AND '.join(conditions)}"
    return query(f"""
        SELECT r.*,
               pr.name as project_name,
               pf.name as portfolio_name
        FROM risks r
        LEFT JOIN projects pr ON r.project_id = pr.project_id
        LEFT JOIN portfolios pf ON r.portfolio_id = pf.portfolio_id
        {where}
        ORDER BY r.risk_score DESC
    """, params=params or None, user_token=user_token,
        sample_fallback=sample_data.get_risks)
