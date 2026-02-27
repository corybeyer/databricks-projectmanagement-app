"""Time Entry Service — time tracking business logic with validation."""

import uuid
from datetime import date
from repositories import time_entry_repo
from utils.validators import validate_time_entry_create, ValidationError


def get_time_entries(project_id: str = None, user_token: str = None):
    """Get all time entries, optionally filtered by project."""
    return time_entry_repo.get_time_entries(project_id=project_id, user_token=user_token)


def get_time_entries_by_task(task_id: str, user_token: str = None):
    """Get all time entries for a specific task."""
    return time_entry_repo.get_time_entries_by_task(task_id, user_token=user_token)


def get_time_entry(entry_id: str, user_token: str = None):
    """Get a single time entry by ID."""
    return time_entry_repo.get_time_entry_by_id(entry_id, user_token=user_token)


def create_time_entry_from_form(form_data: dict, user_email: str = None,
                                user_token: str = None) -> dict:
    """Validate and create a time entry. Returns result dict."""
    try:
        cleaned = validate_time_entry_create(
            task_id=form_data.get("task_id"),
            user_id=form_data.get("user_id"),
            hours=form_data.get("hours"),
            work_date=form_data.get("work_date"),
            notes=form_data.get("notes"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    entry_data = {
        "entry_id": str(uuid.uuid4())[:8],
        "task_id": cleaned["task_id"],
        "user_id": cleaned["user_id"],
        "hours": cleaned["hours"],
        "work_date": str(cleaned["work_date"]),
        "created_by": user_email,
    }

    if cleaned.get("notes"):
        entry_data["notes"] = cleaned["notes"]

    success = time_entry_repo.create_time_entry(entry_data, user_token=user_token)
    if success:
        return {"success": True, "errors": {}, "message": f"Time entry ({cleaned['hours']}h) logged"}
    return {"success": False, "errors": {}, "message": "Failed to create time entry"}


def update_time_entry_from_form(entry_id: str, form_data: dict,
                                expected_updated_at: str, user_email: str = None,
                                user_token: str = None) -> dict:
    """Validate and update a time entry. Returns result dict."""
    try:
        cleaned = validate_time_entry_create(
            task_id=form_data.get("task_id"),
            user_id=form_data.get("user_id"),
            hours=form_data.get("hours"),
            work_date=form_data.get("work_date"),
            notes=form_data.get("notes"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    updates = {
        "task_id": cleaned["task_id"],
        "user_id": cleaned["user_id"],
        "hours": cleaned["hours"],
        "work_date": str(cleaned["work_date"]),
    }

    if cleaned.get("notes") is not None:
        updates["notes"] = cleaned["notes"]

    success = time_entry_repo.update_time_entry(
        entry_id, updates, expected_updated_at,
        user_email=user_email, user_token=user_token,
    )
    if success:
        return {"success": True, "errors": {}, "message": f"Time entry updated ({cleaned['hours']}h)"}
    return {"success": False, "errors": {},
            "message": "Update conflict — record was modified by another user"}


def delete_time_entry(entry_id: str, user_email: str = None,
                      user_token: str = None) -> bool:
    """Soft-delete a time entry."""
    return time_entry_repo.delete_time_entry(
        entry_id, user_email=user_email, user_token=user_token,
    )


def get_time_summary(project_id: str, user_token: str = None):
    """Get aggregated hours per task for a project."""
    return time_entry_repo.get_time_summary_by_task(project_id, user_token=user_token)
