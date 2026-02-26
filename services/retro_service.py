"""Retro Service -- retrospective item CRUD orchestration with validation.

NO Dash imports. Accept/return pure Python types.
"""

import uuid
from repositories import retro_repo
from utils.validators import validate_retro_item_create, ValidationError


def get_retro_items(sprint_id: str, user_token: str = None):
    """Get all retro items for a sprint."""
    return retro_repo.get_retro_items(sprint_id, user_token=user_token)


def get_retro_item(retro_id: str, user_token: str = None):
    """Get a single retro item by ID."""
    return retro_repo.get_retro_item_by_id(retro_id, user_token=user_token)


def create_retro_item_from_form(form_data: dict, user_email: str = None,
                                 user_token: str = None) -> dict:
    """Validate and create a retro item. Returns result dict."""
    try:
        cleaned = validate_retro_item_create(
            category=form_data.get("category"),
            body=form_data.get("body"),
            author=form_data.get("author"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    item_data = {
        "retro_id": f"ret-{str(uuid.uuid4())[:6]}",
        "sprint_id": form_data.get("sprint_id"),
        "category": cleaned["category"],
        "body": cleaned["body"],
        "votes": 0,
        "status": "open",
        "created_by": user_email,
    }
    if cleaned.get("author"):
        item_data["author"] = cleaned["author"]
    else:
        item_data["author"] = user_email

    success = retro_repo.create_retro_item(item_data, user_token=user_token)
    if success:
        return {"success": True, "errors": {},
                "message": "Retro item created"}
    return {"success": False, "errors": {}, "message": "Failed to create retro item"}


def update_retro_item_from_form(retro_id: str, form_data: dict,
                                 expected_updated_at: str,
                                 user_email: str = None,
                                 user_token: str = None) -> dict:
    """Validate and update a retro item. Returns result dict."""
    try:
        cleaned = validate_retro_item_create(
            category=form_data.get("category"),
            body=form_data.get("body"),
            author=form_data.get("author"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    updates = {
        "category": cleaned["category"],
        "body": cleaned["body"],
    }
    if cleaned.get("author"):
        updates["author"] = cleaned["author"]

    success = retro_repo.update_retro_item(
        retro_id, updates, expected_updated_at,
        user_email=user_email, user_token=user_token,
    )
    if success:
        return {"success": True, "errors": {},
                "message": "Retro item updated"}
    return {"success": False, "errors": {},
            "message": "Update conflict -- record was modified by another user"}


def delete_retro_item(retro_id: str, user_email: str = None,
                       user_token: str = None) -> bool:
    """Soft-delete a retro item."""
    return retro_repo.delete_retro_item(
        retro_id, user_email=user_email, user_token=user_token,
    )


def vote_retro_item(retro_id: str, user_email: str = None,
                     user_token: str = None) -> dict:
    """Upvote a retro item. Verify it exists first."""
    item_df = retro_repo.get_retro_item_by_id(retro_id, user_token=user_token)
    if item_df.empty:
        return {"success": False, "message": "Retro item not found"}

    success = retro_repo.vote_retro_item(retro_id, user_token=user_token)
    if success:
        return {"success": True, "message": "Vote recorded"}
    return {"success": False, "message": "Failed to record vote"}


def convert_to_task(retro_id: str, user_email: str = None,
                     user_token: str = None) -> dict:
    """Convert an action item to a task. Must be action or action_item category."""
    item_df = retro_repo.get_retro_item_by_id(retro_id, user_token=user_token)
    if item_df.empty:
        return {"success": False, "message": "Retro item not found"}

    item = item_df.iloc[0]
    category = item.get("category", "")
    if category not in ("action", "action_item"):
        return {"success": False,
                "message": f"Only action items can be converted (current: {category})"}

    current_status = item.get("status", "open")
    if current_status == "converted":
        return {"success": False, "message": "Item is already converted"}

    success = retro_repo.convert_to_task(retro_id, user_token=user_token)
    if success:
        return {"success": True, "message": "Item converted to task"}
    return {"success": False, "message": "Failed to convert item"}
