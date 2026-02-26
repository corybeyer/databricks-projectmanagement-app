"""Risk Repository — risk register queries and CRUD."""

import pandas as pd
from repositories.base import query, write, safe_update, soft_delete
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


def create_risk(risk_data: dict, user_token: str = None) -> bool:
    """Insert a new risk record."""
    allowed_columns = {
        "risk_id", "title", "category", "probability", "impact", "risk_score",
        "status", "mitigation_plan", "response_strategy", "contingency_plan",
        "trigger_conditions", "risk_proximity", "risk_urgency",
        "residual_probability", "residual_impact", "residual_score",
        "secondary_risks", "identified_date", "last_review_date",
        "response_owner", "owner", "project_id", "portfolio_id",
        "created_by", "description",
    }
    params = {}
    used_cols = []
    for col in allowed_columns:
        if col in risk_data:
            if not col.isidentifier():
                raise ValueError(f"Invalid column name: {col!r}")
            used_cols.append(col)
            params[col] = risk_data[col]

    col_list = ", ".join(used_cols)
    param_list = ", ".join(f":{col}" for col in used_cols)
    return write(
        f"INSERT INTO risks ({col_list}) VALUES ({param_list})",
        params=params, user_token=user_token,
        table_name="risks", record=risk_data,
    )


def update_risk(risk_id: str, updates: dict, expected_updated_at: str,
                user_email: str = None, user_token: str = None) -> bool:
    """Update a risk using optimistic locking."""
    return safe_update(
        "risks", "risk_id", risk_id, updates,
        expected_updated_at=expected_updated_at,
        user_email=user_email, user_token=user_token,
    )


def delete_risk(risk_id: str, user_email: str = None,
                user_token: str = None) -> bool:
    """Soft-delete a risk."""
    return soft_delete(
        "risks", "risk_id", risk_id,
        user_email=user_email, user_token=user_token,
    )


def update_risk_status(risk_id: str, new_status: str,
                       user_email: str = None, user_token: str = None) -> bool:
    """Update risk status via safe_update."""
    return safe_update(
        "risks", "risk_id", risk_id,
        {"status": new_status},
        expected_updated_at=None,
        user_email=user_email, user_token=user_token,
    )
