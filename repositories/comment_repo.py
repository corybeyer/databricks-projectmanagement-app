"""Comment Repository — comment queries and CRUD."""

import pandas as pd
from repositories.base import query, write, safe_update, soft_delete
from models import sample_data


def get_comments(task_id: str, user_token: str = None) -> pd.DataFrame:
    """Get all comments for a task, ordered by created_at ascending."""
    return query("""
        SELECT c.*
        FROM comments c
        WHERE c.task_id = :task_id
          AND c.is_deleted = false
        ORDER BY c.created_at ASC
    """, params={"task_id": task_id}, user_token=user_token,
        sample_fallback=sample_data.get_comments)


def get_comment_by_id(comment_id: str, user_token: str = None) -> pd.DataFrame:
    """Get a single comment by ID."""
    return query("""
        SELECT c.*
        FROM comments c
        WHERE c.comment_id = :comment_id
          AND c.is_deleted = false
    """, params={"comment_id": comment_id}, user_token=user_token,
        sample_fallback=sample_data.get_comments)


def create_comment(comment_data: dict, user_token: str = None) -> bool:
    """Insert a new comment record."""
    allowed_columns = {
        "comment_id", "task_id", "author", "body",
        "created_by", "updated_by",
    }
    params = {}
    used_cols = []
    for col in allowed_columns:
        if col in comment_data:
            if not col.isidentifier():
                raise ValueError(f"Invalid column name: {col!r}")
            used_cols.append(col)
            params[col] = comment_data[col]

    col_list = ", ".join(used_cols)
    param_list = ", ".join(f":{col}" for col in used_cols)
    return write(
        f"INSERT INTO comments ({col_list}) VALUES ({param_list})",
        params=params, user_token=user_token,
        table_name="comments", record=comment_data,
    )


def update_comment(comment_id: str, updates: dict, expected_updated_at: str,
                   user_email: str = None, user_token: str = None) -> bool:
    """Update a comment using optimistic locking."""
    return safe_update(
        "comments", "comment_id", comment_id, updates,
        expected_updated_at=expected_updated_at,
        user_email=user_email, user_token=user_token,
    )


def delete_comment(comment_id: str, user_email: str = None,
                   user_token: str = None) -> bool:
    """Soft-delete a comment."""
    return soft_delete(
        "comments", "comment_id", comment_id,
        user_email=user_email, user_token=user_token,
    )


def get_comment_count(task_id: str, user_token: str = None) -> pd.DataFrame:
    """Get count of comments for a task."""
    return query("""
        SELECT COUNT(*) as comment_count
        FROM comments
        WHERE task_id = :task_id
          AND is_deleted = false
    """, params={"task_id": task_id}, user_token=user_token,
        sample_fallback=sample_data.get_comments)
