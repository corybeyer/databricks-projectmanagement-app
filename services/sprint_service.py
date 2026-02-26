"""Sprint Service — sprint management with validation."""

import uuid
from repositories import sprint_repo
from utils.validators import validate_sprint_create, ValidationError


def get_sprints(project_id: str, user_token: str = None):
    return sprint_repo.get_sprints(project_id, user_token=user_token)


def get_sprint_tasks(sprint_id: str, user_token: str = None):
    return sprint_repo.get_sprint_tasks(sprint_id, user_token=user_token)


def get_sprint(sprint_id: str, user_token: str = None):
    return sprint_repo.get_sprint_by_id(sprint_id, user_token=user_token)


def create_sprint_from_form(form_data: dict, user_email: str = None,
                            user_token: str = None) -> dict:
    """Validate and create a sprint. Returns result dict."""
    try:
        cleaned = validate_sprint_create(
            name=form_data.get("name"),
            start_date=form_data.get("start_date"),
            end_date=form_data.get("end_date"),
            capacity_points=form_data.get("capacity_points"),
            goal=form_data.get("goal"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    sprint_data = {
        "sprint_id": str(uuid.uuid4())[:8],
        "name": cleaned["name"],
        "project_id": form_data.get("project_id", "prj-001"),
        "status": "planning",
        "start_date": str(cleaned["start_date"]),
        "end_date": str(cleaned["end_date"]),
        "created_by": user_email,
    }
    if cleaned.get("capacity_points") is not None:
        sprint_data["capacity_points"] = cleaned["capacity_points"]
    if cleaned.get("goal"):
        sprint_data["goal"] = cleaned["goal"]

    success = sprint_repo.create_sprint(sprint_data, user_token=user_token)
    if success:
        return {"success": True, "errors": {}, "message": f"Sprint '{cleaned['name']}' created"}
    return {"success": False, "errors": {}, "message": "Failed to create sprint"}


def close_sprint(sprint_id: str, user_email: str = None,
                 user_token: str = None) -> dict:
    """Close the active sprint. Returns result dict."""
    success = sprint_repo.close_sprint(sprint_id, user_email=user_email,
                                       user_token=user_token)
    if success:
        return {"success": True, "message": "Sprint closed"}
    return {"success": False, "message": "Failed to close sprint — may not be active"}
