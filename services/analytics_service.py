"""Analytics Service — report aggregation."""

from repositories import analytics_repo, risk_repo, resource_repo


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


def get_resource_allocations(user_token: str = None):
    return resource_repo.get_resource_allocations(user_token=user_token)


def get_retro_items(sprint_id: str, user_token: str = None):
    return resource_repo.get_retro_items(sprint_id, user_token=user_token)
