"""Deliverable Service — deliverable tracking with validation."""

import uuid
from datetime import date
from repositories import deliverable_repo
from utils.validators import (
    validate_deliverable_create, validate_enum, ValidationError,
    DELIVERABLE_STATUSES,
)


def get_deliverables(phase_id: str = None, user_token: str = None):
    """Get deliverables, optionally filtered by phase."""
    return deliverable_repo.get_deliverables(phase_id=phase_id, user_token=user_token)


def get_deliverables_by_project(project_id: str, user_token: str = None):
    """Get all deliverables across all phases of a project."""
    return deliverable_repo.get_deliverables_by_project(
        project_id, user_token=user_token,
    )


def get_deliverable(deliverable_id: str, user_token: str = None):
    """Get a single deliverable by ID."""
    return deliverable_repo.get_deliverable_by_id(
        deliverable_id, user_token=user_token,
    )


def create_deliverable_from_form(form_data: dict, user_email: str = None,
                                 user_token: str = None) -> dict:
    """Validate and create a deliverable. Returns result dict."""
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "create", "deliverable"):
        return {"success": False, "message": "Permission denied", "errors": {}}
    try:
        cleaned = validate_deliverable_create(
            name=form_data.get("name"),
            status=form_data.get("status"),
            owner=form_data.get("owner"),
            due_date=form_data.get("due_date"),
            description=form_data.get("description"),
            artifact_url=form_data.get("artifact_url"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message},
                "message": exc.message}

    deliverable_data = {
        "deliverable_id": f"del-{str(uuid.uuid4())[:6]}",
        "name": cleaned["name"],
        "status": cleaned.get("status", "not_started"),
        "phase_id": form_data.get("phase_id", "ph-001"),
        "created_by": user_email,
    }

    # Optional fields
    if cleaned.get("owner"):
        deliverable_data["owner"] = cleaned["owner"]
    if cleaned.get("due_date"):
        deliverable_data["due_date"] = str(cleaned["due_date"])
    if cleaned.get("description"):
        deliverable_data["description"] = cleaned["description"]
    if cleaned.get("artifact_url"):
        deliverable_data["artifact_url"] = cleaned["artifact_url"]

    success = deliverable_repo.create_deliverable(
        deliverable_data, user_token=user_token,
    )
    if success:
        return {"success": True, "errors": {},
                "message": f"Deliverable '{cleaned['name']}' created"}
    return {"success": False, "errors": {}, "message": "Failed to create deliverable"}


def update_deliverable_from_form(deliverable_id: str, form_data: dict,
                                 expected_updated_at: str,
                                 user_email: str = None,
                                 user_token: str = None) -> dict:
    """Validate and update a deliverable. Returns result dict."""
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "update", "deliverable"):
        return {"success": False, "message": "Permission denied", "errors": {}}
    try:
        cleaned = validate_deliverable_create(
            name=form_data.get("name"),
            status=form_data.get("status"),
            owner=form_data.get("owner"),
            due_date=form_data.get("due_date"),
            description=form_data.get("description"),
            artifact_url=form_data.get("artifact_url"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message},
                "message": exc.message}

    updates = {
        "name": cleaned["name"],
        "status": cleaned.get("status", "not_started"),
    }

    # Optional fields - always include if present
    for key in ("owner", "description", "artifact_url"):
        if cleaned.get(key) is not None:
            updates[key] = cleaned[key]
    if cleaned.get("due_date") is not None:
        updates["due_date"] = str(cleaned["due_date"])

    # Phase can change
    phase_id = form_data.get("phase_id")
    if phase_id:
        updates["phase_id"] = phase_id

    success = deliverable_repo.update_deliverable(
        deliverable_id, updates, expected_updated_at,
        user_email=user_email, user_token=user_token,
    )
    if success:
        return {"success": True, "errors": {},
                "message": f"Deliverable '{cleaned['name']}' updated"}
    return {"success": False, "errors": {},
            "message": "Update conflict — record was modified by another user"}


def delete_deliverable(deliverable_id: str, user_email: str = None,
                       user_token: str = None) -> bool:
    """Soft-delete a deliverable."""
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "delete", "deliverable"):
        return False
    return deliverable_repo.delete_deliverable(
        deliverable_id, user_email=user_email, user_token=user_token,
    )


def update_deliverable_status(deliverable_id: str, new_status: str,
                              user_email: str = None,
                              user_token: str = None) -> dict:
    """Update deliverable status."""
    try:
        validated_status = validate_enum(
            new_status, DELIVERABLE_STATUSES, "status",
        )
    except ValidationError as exc:
        return {"success": False, "message": exc.message}

    success = deliverable_repo.update_deliverable_status(
        deliverable_id, validated_status,
        user_email=user_email, user_token=user_token,
    )
    if success:
        label = new_status.replace("_", " ").title()
        return {"success": True, "message": f"Status changed to {label}"}
    return {"success": False, "message": "Failed to update deliverable status"}
