"""Charter Service — charter CRUD orchestration with validation."""

import uuid
from datetime import datetime
from repositories import charter_repo
from utils.validators import validate_charter_create, ValidationError


def get_charters(project_id: str, user_token: str = None):
    """Get all charters for a project."""
    return charter_repo.get_charters(project_id, user_token=user_token)


def get_charter(charter_id: str, user_token: str = None):
    """Get a single charter by ID."""
    return charter_repo.get_charter_by_id(charter_id, user_token=user_token)


def create_charter_from_form(form_data: dict, user_email: str = None,
                              user_token: str = None) -> dict:
    """Validate and create a charter. Returns result dict."""
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "create", "charter"):
        return {"success": False, "message": "Permission denied", "errors": {}}
    try:
        cleaned = validate_charter_create(
            project_name=form_data.get("project_name"),
            business_case=form_data.get("business_case"),
            objectives=form_data.get("objectives"),
            scope_in=form_data.get("scope_in"),
            scope_out=form_data.get("scope_out"),
            stakeholders=form_data.get("stakeholders"),
            success_criteria=form_data.get("success_criteria"),
            risks=form_data.get("risks"),
            budget=form_data.get("budget"),
            timeline=form_data.get("timeline"),
            delivery_method=form_data.get("delivery_method"),
            description=form_data.get("description"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    charter_data = {
        "charter_id": f"ch-{str(uuid.uuid4())[:6]}",
        "project_id": form_data.get("project_id", "prj-001"),
        "project_name": cleaned["project_name"],
        "business_case": cleaned["business_case"],
        "objectives": cleaned["objectives"],
        "scope_in": cleaned["scope_in"],
        "delivery_method": cleaned["delivery_method"],
        "status": "draft",
        "version": 1,
        "created_by": user_email,
        "updated_by": user_email,
    }
    # Add optional fields if present
    for field in ("scope_out", "stakeholders", "success_criteria", "risks",
                  "budget", "timeline", "description"):
        if cleaned.get(field):
            charter_data[field] = cleaned[field]

    success = charter_repo.create_charter(charter_data, user_token=user_token)
    if success:
        return {"success": True, "errors": {},
                "message": f"Charter '{cleaned['project_name']}' created"}
    return {"success": False, "errors": {}, "message": "Failed to create charter"}


def update_charter_from_form(charter_id: str, form_data: dict,
                              expected_updated_at: str,
                              user_email: str = None,
                              user_token: str = None) -> dict:
    """Validate and update a charter. Returns result dict."""
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "update", "charter"):
        return {"success": False, "message": "Permission denied", "errors": {}}
    try:
        cleaned = validate_charter_create(
            project_name=form_data.get("project_name"),
            business_case=form_data.get("business_case"),
            objectives=form_data.get("objectives"),
            scope_in=form_data.get("scope_in"),
            scope_out=form_data.get("scope_out"),
            stakeholders=form_data.get("stakeholders"),
            success_criteria=form_data.get("success_criteria"),
            risks=form_data.get("risks"),
            budget=form_data.get("budget"),
            timeline=form_data.get("timeline"),
            delivery_method=form_data.get("delivery_method"),
            description=form_data.get("description"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    updates = {
        "project_name": cleaned["project_name"],
        "business_case": cleaned["business_case"],
        "objectives": cleaned["objectives"],
        "scope_in": cleaned["scope_in"],
        "delivery_method": cleaned["delivery_method"],
    }
    for field in ("scope_out", "stakeholders", "success_criteria", "risks",
                  "budget", "timeline", "description"):
        if cleaned.get(field) is not None:
            updates[field] = cleaned[field]

    success = charter_repo.update_charter(
        charter_id, updates, expected_updated_at,
        user_email=user_email, user_token=user_token,
    )
    if success:
        return {"success": True, "errors": {},
                "message": f"Charter '{cleaned['project_name']}' updated"}
    return {"success": False, "errors": {},
            "message": "Update conflict — record was modified by another user"}


def submit_charter(charter_id: str, user_email: str = None,
                    user_token: str = None) -> dict:
    """Change charter status from draft to submitted."""
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "update", "charter"):
        return {"success": False, "message": "Permission denied"}
    charter_df = charter_repo.get_charter_by_id(charter_id, user_token=user_token)
    if charter_df.empty:
        return {"success": False, "message": "Charter not found"}

    current_status = charter_df.iloc[0].get("status", "draft")
    if current_status not in ("draft", "rejected"):
        return {"success": False,
                "message": f"Cannot submit — charter is '{current_status}', must be 'draft' or 'rejected'"}

    success = charter_repo.update_charter_status(
        charter_id, "submitted", user_email=user_email, user_token=user_token,
    )
    if success:
        return {"success": True, "message": "Charter submitted for approval"}
    return {"success": False, "message": "Failed to submit charter"}


def approve_charter(charter_id: str, user_email: str = None,
                     user_token: str = None) -> dict:
    """Approve a submitted charter."""
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "approve", "charter"):
        return {"success": False, "message": "Permission denied — approval requires lead/pm role"}
    charter_df = charter_repo.get_charter_by_id(charter_id, user_token=user_token)
    if charter_df.empty:
        return {"success": False, "message": "Charter not found"}

    current_status = charter_df.iloc[0].get("status", "draft")
    if current_status not in ("submitted", "under_review"):
        return {"success": False,
                "message": f"Cannot approve — charter is '{current_status}', must be 'submitted' or 'under_review'"}

    updates = {
        "status": "approved",
        "approved_by": user_email or "unknown",
        "approved_date": datetime.now().strftime("%Y-%m-%d"),
    }
    expected = str(charter_df.iloc[0].get("updated_at", ""))
    success = charter_repo.update_charter(
        charter_id, updates, expected_updated_at=expected or None,
        user_email=user_email, user_token=user_token,
    )
    if success:
        return {"success": True, "message": "Charter approved"}
    return {"success": False, "message": "Failed to approve charter"}


def reject_charter(charter_id: str, user_email: str = None,
                    user_token: str = None) -> dict:
    """Reject a submitted charter."""
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "approve", "charter"):
        return {"success": False, "message": "Permission denied — rejection requires lead/pm role"}
    charter_df = charter_repo.get_charter_by_id(charter_id, user_token=user_token)
    if charter_df.empty:
        return {"success": False, "message": "Charter not found"}

    current_status = charter_df.iloc[0].get("status", "draft")
    if current_status not in ("submitted", "under_review"):
        return {"success": False,
                "message": f"Cannot reject — charter is '{current_status}', must be 'submitted' or 'under_review'"}

    success = charter_repo.update_charter_status(
        charter_id, "rejected", user_email=user_email, user_token=user_token,
    )
    if success:
        return {"success": True, "message": "Charter rejected"}
    return {"success": False, "message": "Failed to reject charter"}


def delete_charter(charter_id: str, user_email: str = None,
                    user_token: str = None) -> bool:
    """Soft-delete a charter."""
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "delete", "charter"):
        return False
    return charter_repo.delete_charter(
        charter_id, user_email=user_email, user_token=user_token,
    )
