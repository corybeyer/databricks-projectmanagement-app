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


def get_risk_detail(risk_id: str, user_token: str = None) -> pd.DataFrame:
    """Get a single risk with all PMI fields."""
    return query("""
        SELECT r.*,
               pr.name as project_name,
               pf.name as portfolio_name
        FROM risks r
        LEFT JOIN projects pr ON r.project_id = pr.project_id
        LEFT JOIN portfolios pf ON r.portfolio_id = pf.portfolio_id
        WHERE r.risk_id = :risk_id
          AND r.is_deleted = false
    """, params={"risk_id": risk_id}, user_token=user_token,
        sample_fallback=sample_data.get_risks)


def get_risks_by_project(project_id: str, user_token: str = None) -> pd.DataFrame:
    """Get all risks for a specific project."""
    return query("""
        SELECT r.*,
               pr.name as project_name,
               pf.name as portfolio_name
        FROM risks r
        LEFT JOIN projects pr ON r.project_id = pr.project_id
        LEFT JOIN portfolios pf ON r.portfolio_id = pf.portfolio_id
        WHERE r.project_id = :project_id
          AND r.is_deleted = false
        ORDER BY r.risk_score DESC
    """, params={"project_id": project_id}, user_token=user_token,
        sample_fallback=sample_data.get_risks)


def get_risks_overdue_review(days_threshold: int = 14, user_token: str = None) -> pd.DataFrame:
    """Get risks that haven't been reviewed within the threshold."""
    return query("""
        SELECT r.*,
               pr.name as project_name,
               pf.name as portfolio_name
        FROM risks r
        LEFT JOIN projects pr ON r.project_id = pr.project_id
        LEFT JOIN portfolios pf ON r.portfolio_id = pf.portfolio_id
        WHERE r.is_deleted = false
          AND r.status NOT IN ('resolved', 'closed')
          AND (r.last_review_date IS NULL
               OR datediff(current_date(), r.last_review_date) > :days_threshold)
        ORDER BY r.risk_score DESC
    """, params={"days_threshold": days_threshold}, user_token=user_token,
        sample_fallback=sample_data.get_risks)
