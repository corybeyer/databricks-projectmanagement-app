"""Department Repository — organizational hierarchy queries."""

import pandas as pd
from repositories.base import query
from models import sample_data


def get_departments(user_token: str = None) -> pd.DataFrame:
    return query("""
        SELECT d.*,
               p.name as parent_name
        FROM departments d
        LEFT JOIN departments p ON d.parent_dept_id = p.department_id
        WHERE d.is_deleted = false
        ORDER BY d.name
    """, user_token=user_token, sample_fallback=sample_data.get_departments)


def get_department(department_id: str, user_token: str = None) -> pd.DataFrame:
    return query("""
        SELECT d.*,
               p.name as parent_name
        FROM departments d
        LEFT JOIN departments p ON d.parent_dept_id = p.department_id
        WHERE d.department_id = :department_id
          AND d.is_deleted = false
    """, params={"department_id": department_id}, user_token=user_token,
        sample_fallback=sample_data.get_departments)


def get_department_hierarchy(user_token: str = None) -> pd.DataFrame:
    return query("""
        SELECT d.department_id, d.name, d.description, d.head,
               d.parent_dept_id, p.name as parent_name,
               COUNT(DISTINCT port.portfolio_id) as portfolio_count,
               COUNT(DISTINCT tm.user_id) as member_count
        FROM departments d
        LEFT JOIN departments p ON d.parent_dept_id = p.department_id
        LEFT JOIN portfolios port ON d.department_id = port.department_id AND port.is_deleted = false
        LEFT JOIN team_members tm ON d.department_id = tm.department_id AND tm.is_active = true
        WHERE d.is_deleted = false
        GROUP BY d.department_id, d.name, d.description, d.head,
                 d.parent_dept_id, p.name
        ORDER BY d.name
    """, user_token=user_token, sample_fallback=sample_data.get_departments)
