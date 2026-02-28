"""Analytics Service — report aggregation.

Read functions enforce RBAC department filtering where applicable.
Functions scoped by project_id or sprint_id are already implicitly
scoped through URL context; only "list all" entry points apply filtering.
"""

from repositories import analytics_repo, risk_repo, resource_repo, retro_repo


def get_velocity(project_id: str, user_token: str = None):
    return analytics_repo.get_velocity(project_id, user_token=user_token)


def get_burndown(sprint_id: str, user_token: str = None):
    return analytics_repo.get_burndown(sprint_id, user_token=user_token)


def get_cycle_times(project_id: str, user_token: str = None):
    return analytics_repo.get_status_cycle_times(project_id, user_token=user_token)


def get_gate_status(project_id: str, user_token: str = None):
    return analytics_repo.get_gate_status(project_id, user_token=user_token)


def get_risks(portfolio_id: str = None, user_token: str = None):
    return risk_repo.get_risks(portfolio_id=portfolio_id, user_token=user_token)


def get_risks_by_project(project_id: str, user_token: str = None):
    return risk_repo.get_risks_by_project(project_id, user_token=user_token)


def get_risks_overdue_review(days_threshold: int = 14, user_token: str = None):
    return risk_repo.get_risks_overdue_review(days_threshold=days_threshold, user_token=user_token)


def get_resource_allocations(department_id: str = None, user_token: str = None):
    """Get resource allocations, enforcing RBAC department filtering.

    Non-admin users only see team members from their own department.
    The filtering is applied post-query on department_id column.
    """
    from services.auth_service import get_current_user, get_department_filter
    user = get_current_user()
    dept = get_department_filter(user)
    effective_dept = dept if dept is not None else department_id

    df = resource_repo.get_resource_allocations(user_token=user_token)
    if effective_dept and not df.empty and "department_id" in df.columns:
        df = df[df["department_id"] == effective_dept]
    return df


def get_retro_items(sprint_id: str, user_token: str = None):
    return retro_repo.get_retro_items(sprint_id, user_token=user_token)
