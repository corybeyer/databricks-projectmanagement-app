"""Project Service — project CRUD orchestration, detail, and charter retrieval."""

import uuid
from repositories import project_repo, charter_repo
from utils.validators import validate_project_create, ValidationError


def get_project_detail(project_id: str, user_token: str = None):
    return project_repo.get_project_detail(project_id, user_token=user_token)


def get_project_charter(project_id: str, user_token: str = None):
    return charter_repo.get_project_charter(project_id, user_token=user_token)


def get_project_phases(project_id: str, user_token: str = None):
    return project_repo.get_project_phases(project_id, user_token=user_token)


def get_projects(portfolio_id: str = None, user_token: str = None):
    """Get all non-deleted projects, optionally filtered by portfolio."""
    return project_repo.get_projects(portfolio_id=portfolio_id, user_token=user_token)


def get_project(project_id: str, user_token: str = None):
    """Get a single project by ID."""
    return project_repo.get_project_by_id(project_id, user_token=user_token)


def create_project_from_form(form_data: dict, user_email: str = None,
                             user_token: str = None) -> dict:
    """Validate and create a project. Returns result dict."""
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "create", "project"):
        return {"success": False, "message": "Permission denied", "errors": {}}
    try:
        cleaned = validate_project_create(
            name=form_data.get("name"),
            delivery_method=form_data.get("delivery_method"),
            status=form_data.get("status"),
            health=form_data.get("health"),
            start_date=form_data.get("start_date"),
            owner=form_data.get("owner"),
            description=form_data.get("description"),
            target_date=form_data.get("target_date"),
            budget_total=form_data.get("budget_total"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    project_data = {
        "project_id": f"prj-{str(uuid.uuid4())[:6]}",
        "name": cleaned["name"],
        "delivery_method": cleaned["delivery_method"],
        "status": cleaned["status"],
        "health": cleaned["health"],
        "start_date": str(cleaned["start_date"]),
        "owner": cleaned["owner"],
        "portfolio_id": form_data.get("portfolio_id", "pf-001"),
        "department_id": form_data.get("department_id", "dept-001"),
        "budget_spent": 0,
        "pct_complete": 0,
        "created_by": user_email,
    }

    # Optional fields
    if cleaned.get("description"):
        project_data["description"] = cleaned["description"]
    if cleaned.get("target_date"):
        project_data["target_date"] = str(cleaned["target_date"])
    if cleaned.get("budget_total") is not None:
        project_data["budget_total"] = cleaned["budget_total"]

    success = project_repo.create_project(project_data, user_token=user_token)
    if success:
        return {"success": True, "errors": {},
                "message": f"Project '{cleaned['name']}' created"}
    return {"success": False, "errors": {}, "message": "Failed to create project"}


def update_project_from_form(project_id: str, form_data: dict,
                             expected_updated_at: str,
                             user_email: str = None,
                             user_token: str = None) -> dict:
    """Validate and update a project. Returns result dict."""
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "update", "project"):
        return {"success": False, "message": "Permission denied", "errors": {}}
    try:
        cleaned = validate_project_create(
            name=form_data.get("name"),
            delivery_method=form_data.get("delivery_method"),
            status=form_data.get("status"),
            health=form_data.get("health"),
            start_date=form_data.get("start_date"),
            owner=form_data.get("owner"),
            description=form_data.get("description"),
            target_date=form_data.get("target_date"),
            budget_total=form_data.get("budget_total"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    updates = {
        "name": cleaned["name"],
        "delivery_method": cleaned["delivery_method"],
        "status": cleaned["status"],
        "health": cleaned["health"],
        "start_date": str(cleaned["start_date"]),
        "owner": cleaned["owner"],
    }

    for field in ("description",):
        if cleaned.get(field) is not None:
            updates[field] = cleaned[field]
    if cleaned.get("target_date") is not None:
        updates["target_date"] = str(cleaned["target_date"])
    if cleaned.get("budget_total") is not None:
        updates["budget_total"] = cleaned["budget_total"]

    success = project_repo.update_project(
        project_id, updates, expected_updated_at,
        user_email=user_email, user_token=user_token,
    )
    if success:
        return {"success": True, "errors": {},
                "message": f"Project '{cleaned['name']}' updated"}
    return {"success": False, "errors": {},
            "message": "Update conflict — record was modified by another user"}


def delete_project(project_id: str, user_email: str = None,
                   user_token: str = None) -> bool:
    """Soft-delete a project."""
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "delete", "project"):
        return False
    return project_repo.delete_project(
        project_id, user_email=user_email, user_token=user_token,
    )
