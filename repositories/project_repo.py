"""Project Repository — project CRUD, detail, and phase queries."""

import pandas as pd
from repositories.base import query, write, safe_update, soft_delete
from models import sample_data


def get_projects(portfolio_id: str = None, department_id: str = None,
                  user_token: str = None) -> pd.DataFrame:
    """Get all non-deleted projects, optionally filtered by portfolio or department."""
    if portfolio_id:
        return query("""
            SELECT pr.*,
                   pf.name as portfolio_name,
                   ph.name as current_phase_name,
                   ph.phase_type,
                   s.name as active_sprint_name,
                   s.sprint_id as active_sprint_id
            FROM projects pr
            LEFT JOIN portfolios pf ON pr.portfolio_id = pf.portfolio_id
            LEFT JOIN phases ph ON pr.current_phase_id = ph.phase_id
            LEFT JOIN sprints s ON pr.project_id = s.project_id AND s.status = 'active'
            WHERE pr.portfolio_id = :portfolio_id
              AND pr.is_deleted = false
            ORDER BY pr.priority_rank
        """, params={"portfolio_id": portfolio_id}, user_token=user_token,
            sample_fallback=sample_data.get_portfolio_projects)
    if department_id:
        return query("""
            SELECT pr.*,
                   pf.name as portfolio_name,
                   ph.name as current_phase_name,
                   ph.phase_type,
                   s.name as active_sprint_name,
                   s.sprint_id as active_sprint_id
            FROM projects pr
            JOIN portfolios pf ON pr.portfolio_id = pf.portfolio_id
            LEFT JOIN phases ph ON pr.current_phase_id = ph.phase_id
            LEFT JOIN sprints s ON pr.project_id = s.project_id AND s.status = 'active'
            WHERE pf.department_id = :department_id
              AND pr.is_deleted = false
            ORDER BY pr.priority_rank
        """, params={"department_id": department_id}, user_token=user_token,
            sample_fallback=sample_data.get_portfolio_projects)
    return query("""
        SELECT pr.*,
               pf.name as portfolio_name,
               ph.name as current_phase_name,
               ph.phase_type,
               s.name as active_sprint_name,
               s.sprint_id as active_sprint_id
        FROM projects pr
        LEFT JOIN portfolios pf ON pr.portfolio_id = pf.portfolio_id
        LEFT JOIN phases ph ON pr.current_phase_id = ph.phase_id
        LEFT JOIN sprints s ON pr.project_id = s.project_id AND s.status = 'active'
        WHERE pr.is_deleted = false
        ORDER BY pr.priority_rank
    """, user_token=user_token, sample_fallback=sample_data.get_portfolio_projects)


def get_project_by_id(project_id: str, user_token: str = None) -> pd.DataFrame:
    """Get a single project by ID."""
    return query("""
        SELECT pr.*,
               pf.name as portfolio_name,
               ph.name as current_phase_name,
               ph.delivery_method as phase_delivery_method
        FROM projects pr
        LEFT JOIN portfolios pf ON pr.portfolio_id = pf.portfolio_id
        LEFT JOIN phases ph ON pr.current_phase_id = ph.phase_id
        WHERE pr.project_id = :project_id
          AND pr.is_deleted = false
    """, params={"project_id": project_id}, user_token=user_token,
        sample_fallback=sample_data.get_project_detail)


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
          AND pr.is_deleted = false
    """, params={"project_id": project_id}, user_token=user_token,
        sample_fallback=sample_data.get_project_detail)


def get_project_phases(project_id: str, user_token: str = None) -> pd.DataFrame:
    return query("""
        SELECT ph.*,
               COUNT(DISTINCT t.task_id) as task_count,
               COUNT(DISTINCT CASE WHEN t.status = 'done' THEN t.task_id END) as done_count
        FROM phases ph
        LEFT JOIN tasks t ON ph.phase_id = t.phase_id
        WHERE ph.project_id = :project_id
          AND ph.is_deleted = false
        GROUP BY ALL
        ORDER BY ph.phase_order
    """, params={"project_id": project_id}, user_token=user_token,
        sample_fallback=sample_data.get_project_phases)


def create_project(project_data: dict, user_token: str = None) -> bool:
    """Insert a new project. Uses allowed_columns whitelist."""
    allowed_columns = {
        "project_id", "name", "portfolio_id", "department_id", "status",
        "health", "delivery_method", "description", "owner", "sponsor",
        "start_date", "target_date", "budget_total", "budget_spent",
        "pct_complete", "priority_rank", "created_by",
    }
    params = {}
    used_cols = []
    for col in allowed_columns:
        if col in project_data:
            if not col.isidentifier():
                raise ValueError(f"Invalid column name: {col!r}")
            used_cols.append(col)
            params[col] = project_data[col]

    col_list = ", ".join(used_cols)
    param_list = ", ".join(f":{col}" for col in used_cols)
    return write(
        f"INSERT INTO projects ({col_list}) VALUES ({param_list})",
        params=params, user_token=user_token,
        table_name="projects", record=project_data,
    )


def update_project(project_id: str, updates: dict, expected_updated_at: str,
                   user_email: str = None, user_token: str = None) -> bool:
    """Update a project via optimistic locking."""
    return safe_update(
        "projects", "project_id", project_id, updates,
        expected_updated_at=expected_updated_at,
        user_email=user_email, user_token=user_token,
    )


def delete_project(project_id: str, user_email: str = None,
                   user_token: str = None) -> bool:
    """Soft-delete a project."""
    return soft_delete(
        "projects", "project_id", project_id,
        user_email=user_email, user_token=user_token,
    )
