"""Project Service — project detail and charter retrieval."""

from repositories import project_repo, charter_repo


def get_project_detail(project_id: str, user_token: str = None):
    return project_repo.get_project_detail(project_id, user_token=user_token)


def get_project_charter(project_id: str, user_token: str = None):
    return charter_repo.get_project_charter(project_id, user_token=user_token)


def get_project_phases(project_id: str, user_token: str = None):
    return project_repo.get_project_phases(project_id, user_token=user_token)
