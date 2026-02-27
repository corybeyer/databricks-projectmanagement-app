"""Dependency Service — cross-project dependency management with validation."""

import uuid
from repositories import dependency_repo
from utils.validators import (
    validate_dependency_create, validate_enum, ValidationError,
    DEPENDENCY_STATUSES,
)


def get_dependencies(project_id: str = None, user_token: str = None):
    """Get all dependencies, optionally filtered by project."""
    return dependency_repo.get_dependencies(project_id=project_id, user_token=user_token)


def get_dependency(dependency_id: str, user_token: str = None):
    """Get a single dependency by ID."""
    return dependency_repo.get_dependency_by_id(dependency_id, user_token=user_token)


def create_dependency_from_form(form_data: dict, user_email: str = None,
                                user_token: str = None) -> dict:
    """Validate and create a dependency. Returns result dict."""
    try:
        cleaned = validate_dependency_create(
            source_project_id=form_data.get("source_project_id"),
            target_project_id=form_data.get("target_project_id"),
            dependency_type=form_data.get("dependency_type"),
            risk_level=form_data.get("risk_level"),
            description=form_data.get("description"),
            status=form_data.get("status"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    dep_data = {
        "dependency_id": str(uuid.uuid4())[:8],
        "source_project_id": cleaned["source_project_id"],
        "target_project_id": cleaned["target_project_id"],
        "dependency_type": cleaned["dependency_type"],
        "risk_level": cleaned["risk_level"],
        "status": cleaned.get("status") or "active",
        "created_by": user_email,
    }

    # Optional fields
    if cleaned.get("description"):
        dep_data["description"] = cleaned["description"]
    if form_data.get("source_task_id"):
        dep_data["source_task_id"] = form_data["source_task_id"]
    if form_data.get("target_task_id"):
        dep_data["target_task_id"] = form_data["target_task_id"]

    success = dependency_repo.create_dependency(dep_data, user_token=user_token)
    if success:
        return {"success": True, "errors": {}, "message": "Dependency created"}
    return {"success": False, "errors": {}, "message": "Failed to create dependency"}


def update_dependency_from_form(dependency_id: str, form_data: dict,
                                expected_updated_at: str,
                                user_email: str = None,
                                user_token: str = None) -> dict:
    """Validate and update a dependency. Returns result dict."""
    try:
        cleaned = validate_dependency_create(
            source_project_id=form_data.get("source_project_id"),
            target_project_id=form_data.get("target_project_id"),
            dependency_type=form_data.get("dependency_type"),
            risk_level=form_data.get("risk_level"),
            description=form_data.get("description"),
            status=form_data.get("status"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    updates = {
        "source_project_id": cleaned["source_project_id"],
        "target_project_id": cleaned["target_project_id"],
        "dependency_type": cleaned["dependency_type"],
        "risk_level": cleaned["risk_level"],
    }

    if cleaned.get("status"):
        updates["status"] = cleaned["status"]
    if cleaned.get("description") is not None:
        updates["description"] = cleaned["description"]

    success = dependency_repo.update_dependency(
        dependency_id, updates, expected_updated_at,
        user_email=user_email, user_token=user_token,
    )
    if success:
        return {"success": True, "errors": {}, "message": "Dependency updated"}
    return {"success": False, "errors": {},
            "message": "Update conflict — record was modified by another user"}


def delete_dependency(dependency_id: str, user_email: str = None,
                      user_token: str = None) -> bool:
    """Soft-delete a dependency."""
    return dependency_repo.delete_dependency(
        dependency_id, user_email=user_email, user_token=user_token,
    )


def update_dependency_status(dependency_id: str, new_status: str,
                             user_email: str = None,
                             user_token: str = None) -> dict:
    """Update dependency status. Returns result dict."""
    try:
        validated_status = validate_enum(new_status, DEPENDENCY_STATUSES, "status")
    except ValidationError as exc:
        return {"success": False, "message": exc.message}

    success = dependency_repo.update_dependency(
        dependency_id, {"status": validated_status},
        expected_updated_at=None,
        user_email=user_email, user_token=user_token,
    )
    if success:
        label = new_status.replace("_", " ").title()
        return {"success": True, "message": f"Status changed to {label}"}
    return {"success": False, "message": "Failed to update dependency status"}


def resolve_dependency(dependency_id: str, user_email: str = None,
                       user_token: str = None) -> dict:
    """Mark a dependency as resolved."""
    success = dependency_repo.resolve_dependency(
        dependency_id, user_email=user_email, user_token=user_token,
    )
    if success:
        return {"success": True, "message": "Dependency resolved"}
    return {"success": False, "message": "Failed to resolve dependency"}
