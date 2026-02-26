"""Sprint Service — sprint management."""

from repositories import sprint_repo


def get_sprints(project_id: str, user_token: str = None):
    return sprint_repo.get_sprints(project_id, user_token=user_token)


def get_sprint_tasks(sprint_id: str, user_token: str = None):
    return sprint_repo.get_sprint_tasks(sprint_id, user_token=user_token)
