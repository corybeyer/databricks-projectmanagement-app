"""Comment Service — comment management with validation."""

import uuid
from repositories import comment_repo
from utils.validators import validate_comment_create, ValidationError


def get_comments(task_id: str, user_token: str = None):
    """Get all comments for a task."""
    return comment_repo.get_comments(task_id, user_token=user_token)


def get_comment(comment_id: str, user_token: str = None):
    """Get a single comment by ID."""
    return comment_repo.get_comment_by_id(comment_id, user_token=user_token)


def create_comment_from_form(task_id: str, body: str, user_email: str = None,
                              user_token: str = None) -> dict:
    """Validate and create a comment. Returns result dict."""
    try:
        cleaned = validate_comment_create(body=body, author=user_email)
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    comment_data = {
        "comment_id": f"cmt-{str(uuid.uuid4())[:6]}",
        "task_id": task_id,
        "author": user_email or "anonymous",
        "body": cleaned["body"],
        "created_by": user_email,
        "updated_by": user_email,
    }

    success = comment_repo.create_comment(comment_data, user_token=user_token)
    if success:
        return {"success": True, "errors": {}, "message": "Comment added"}
    return {"success": False, "errors": {}, "message": "Failed to add comment"}


def update_comment_from_form(comment_id: str, body: str, expected_updated_at: str,
                              user_email: str = None, user_token: str = None) -> dict:
    """Validate and update a comment. Returns result dict."""
    try:
        cleaned = validate_comment_create(body=body, author=user_email)
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    updates = {"body": cleaned["body"]}

    success = comment_repo.update_comment(
        comment_id, updates, expected_updated_at,
        user_email=user_email, user_token=user_token,
    )
    if success:
        return {"success": True, "errors": {}, "message": "Comment updated"}
    return {"success": False, "errors": {},
            "message": "Update conflict — comment was modified by another user"}


def delete_comment(comment_id: str, user_email: str = None,
                   user_token: str = None) -> bool:
    """Soft-delete a comment."""
    return comment_repo.delete_comment(comment_id, user_email=user_email,
                                        user_token=user_token)


def get_comment_count(task_id: str, user_token: str = None):
    """Get count of comments for a task."""
    return comment_repo.get_comment_count(task_id, user_token=user_token)
