"""Portfolio Repository — portfolio CRUD and portfolio-project queries."""

import pandas as pd
from repositories.base import query, write, safe_update, soft_delete
from models import sample_data


def get_portfolios(department_id: str = None, user_token: str = None) -> pd.DataFrame:
    if department_id:
        return query("""
            SELECT p.*,
                   COUNT(DISTINCT pr.project_id) as project_count,
                   AVG(pr.pct_complete) as avg_completion,
                   SUM(pr.budget_spent) as total_spent,
                   SUM(pr.budget_total) as total_budget
            FROM portfolios p
            LEFT JOIN projects pr ON p.portfolio_id = pr.portfolio_id AND pr.is_deleted = false
            WHERE p.is_deleted = false
              AND p.department_id = :department_id
            GROUP BY ALL
            ORDER BY p.name
        """, params={"department_id": department_id},
            user_token=user_token, sample_fallback=sample_data.get_portfolios)
    return query("""
        SELECT p.*,
               COUNT(DISTINCT pr.project_id) as project_count,
               AVG(pr.pct_complete) as avg_completion,
               SUM(pr.budget_spent) as total_spent,
               SUM(pr.budget_total) as total_budget
        FROM portfolios p
        LEFT JOIN projects pr ON p.portfolio_id = pr.portfolio_id AND pr.is_deleted = false
        WHERE p.is_deleted = false
        GROUP BY ALL
        ORDER BY p.name
    """, user_token=user_token, sample_fallback=sample_data.get_portfolios)


def get_portfolio_by_id(portfolio_id: str, user_token: str = None) -> pd.DataFrame:
    """Get a single portfolio by ID."""
    return query(
        "SELECT * FROM portfolios WHERE portfolio_id = :portfolio_id AND is_deleted = false",
        params={"portfolio_id": portfolio_id}, user_token=user_token,
        sample_fallback=sample_data.get_portfolios,
    )


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
          AND pr.is_deleted = false
        ORDER BY pr.priority_rank
    """, params={"portfolio_id": portfolio_id}, user_token=user_token,
        sample_fallback=sample_data.get_portfolio_projects)


def create_portfolio(portfolio_data: dict, user_token: str = None) -> bool:
    """Insert a new portfolio. Uses allowed_columns whitelist."""
    allowed_columns = {
        "portfolio_id", "name", "owner", "department_id", "status",
        "health", "description", "strategic_priority", "created_by",
    }
    params = {}
    used_cols = []
    for col in allowed_columns:
        if col in portfolio_data:
            if not col.isidentifier():
                raise ValueError(f"Invalid column name: {col!r}")
            used_cols.append(col)
            params[col] = portfolio_data[col]

    col_list = ", ".join(used_cols)
    param_list = ", ".join(f":{col}" for col in used_cols)
    return write(
        f"INSERT INTO portfolios ({col_list}) VALUES ({param_list})",
        params=params, user_token=user_token,
        table_name="portfolios", record=portfolio_data,
    )


def update_portfolio(portfolio_id: str, updates: dict, expected_updated_at: str,
                     user_email: str = None, user_token: str = None) -> bool:
    """Update a portfolio via optimistic locking."""
    return safe_update(
        "portfolios", "portfolio_id", portfolio_id, updates,
        expected_updated_at=expected_updated_at,
        user_email=user_email, user_token=user_token,
    )


def delete_portfolio(portfolio_id: str, user_email: str = None,
                     user_token: str = None) -> bool:
    """Soft-delete a portfolio."""
    return soft_delete(
        "portfolios", "portfolio_id", portfolio_id,
        user_email=user_email, user_token=user_token,
    )
