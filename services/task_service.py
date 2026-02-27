"""Task Service — task CRUD orchestration with validation."""

import uuid
from repositories import task_repo
from utils.validators import validate_task_create, ValidationError


def get_tasks(user_token: str = None):
    """Get all tasks across all projects."""
    return task_repo.get_all_tasks(user_token=user_token)


def get_backlog(project_id: str, user_token: str = None):
    return task_repo.get_backlog(project_id, user_token=user_token)


def get_task(task_id: str, user_token: str = None):
    return task_repo.get_task_by_id(task_id, user_token=user_token)


def create_task_from_form(form_data: dict, user_email: str = None,
                          user_token: str = None) -> dict:
    """Validate and create a task. Returns result dict."""
    try:
        cleaned = validate_task_create(
            title=form_data.get("title"),
            task_type=form_data.get("task_type"),
            priority=form_data.get("priority"),
            story_points=form_data.get("story_points"),
            assignee=form_data.get("assignee"),
            description=form_data.get("description"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    task_data = {
        "task_id": str(uuid.uuid4())[:8],
        "title": cleaned["title"],
        "task_type": cleaned["task_type"],
        "priority": cleaned["priority"],
        "status": form_data.get("status", "todo"),
        "project_id": form_data.get("project_id", "prj-001"),
        "sprint_id": form_data.get("sprint_id"),
        "created_by": user_email,
    }
    if cleaned.get("story_points") is not None:
        task_data["story_points"] = cleaned["story_points"]
    if cleaned.get("assignee"):
        task_data["assignee"] = cleaned["assignee"]
    if cleaned.get("description"):
        task_data["description"] = cleaned["description"]

    success = task_repo.create_task(task_data, user_token=user_token)
    if success:
        return {"success": True, "errors": {}, "message": f"Task '{cleaned['title']}' created"}
    return {"success": False, "errors": {}, "message": "Failed to create task"}


def update_task_from_form(task_id: str, form_data: dict, expected_updated_at: str,
                          user_email: str = None, user_token: str = None) -> dict:
    """Validate and update a task. Returns result dict."""
    try:
        cleaned = validate_task_create(
            title=form_data.get("title"),
            task_type=form_data.get("task_type"),
            priority=form_data.get("priority"),
            story_points=form_data.get("story_points"),
            assignee=form_data.get("assignee"),
            description=form_data.get("description"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    updates = {
        "title": cleaned["title"],
        "task_type": cleaned["task_type"],
        "priority": cleaned["priority"],
    }
    if cleaned.get("story_points") is not None:
        updates["story_points"] = cleaned["story_points"]
    if cleaned.get("assignee") is not None:
        updates["assignee"] = cleaned["assignee"]
    if cleaned.get("description") is not None:
        updates["description"] = cleaned["description"]

    success = task_repo.update_task(
        task_id, updates, expected_updated_at,
        user_email=user_email, user_token=user_token,
    )
    if success:
        return {"success": True, "errors": {}, "message": f"Task '{cleaned['title']}' updated"}
    return {"success": False, "errors": {},
            "message": "Update conflict — record was modified by another user"}


def delete_task(task_id: str, user_email: str = None, user_token: str = None) -> bool:
    return task_repo.delete_task(task_id, user_email=user_email, user_token=user_token)


def update_task_status(task_id: str, new_status: str, changed_by: str,
                       user_token: str = None) -> bool:
    return task_repo.update_task_status(task_id, new_status, changed_by,
                                        user_token=user_token)


def move_task_to_sprint(task_id: str, sprint_id: str, user_token: str = None) -> bool:
    return task_repo.move_task_to_sprint(task_id, sprint_id, user_token=user_token)
