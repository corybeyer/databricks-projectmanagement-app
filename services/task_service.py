"""Task Service — task CRUD orchestration."""

from repositories import task_repo


def get_backlog(project_id: str, user_token: str = None):
    return task_repo.get_backlog(project_id, user_token=user_token)


def create_task(task_data: dict, user_token: str = None) -> bool:
    return task_repo.create_task(task_data, user_token=user_token)


def update_task_status(task_id: str, new_status: str, changed_by: str,
                       user_token: str = None) -> bool:
    return task_repo.update_task_status(task_id, new_status, changed_by, user_token=user_token)


def move_task_to_sprint(task_id: str, sprint_id: str, user_token: str = None) -> bool:
    return task_repo.move_task_to_sprint(task_id, sprint_id, user_token=user_token)
