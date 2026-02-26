"""Retro Repository -- retrospective item CRUD operations."""

import pandas as pd
from repositories.base import query, write, safe_update, soft_delete
from models import sample_data


def get_retro_items(sprint_id: str, user_token: str = None) -> pd.DataFrame:
    """Get all non-deleted retro items for a sprint, ordered by votes DESC."""
    return query("""
        SELECT r.*
        FROM retro_items r
        WHERE r.sprint_id = :sprint_id
          AND r.is_deleted = false
        ORDER BY r.votes DESC
    """, params={"sprint_id": sprint_id}, user_token=user_token,
        sample_fallback=sample_data.get_retro_items)


def get_retro_item_by_id(retro_id: str, user_token: str = None) -> pd.DataFrame:
    """Get a single retro item by ID."""
    return query(
        "SELECT * FROM retro_items WHERE retro_id = :retro_id AND is_deleted = false",
        params={"retro_id": retro_id}, user_token=user_token,
        sample_fallback=sample_data.get_retro_items,
    )


def create_retro_item(item_data: dict, user_token: str = None) -> bool:
    """Insert a new retro item. Uses allowed_columns whitelist."""
    allowed_columns = {
        "retro_id", "sprint_id", "category", "body", "votes",
        "author", "status", "created_by",
    }
    params = {}
    used_cols = []
    for col in allowed_columns:
        if col in item_data:
            if not col.isidentifier():
                raise ValueError(f"Invalid column name: {col!r}")
            used_cols.append(col)
            params[col] = item_data[col]

    col_list = ", ".join(used_cols)
    param_list = ", ".join(f":{col}" for col in used_cols)
    return write(
        f"INSERT INTO retro_items ({col_list}) VALUES ({param_list})",
        params=params, user_token=user_token,
        table_name="retro_items", record=item_data,
    )


def update_retro_item(retro_id: str, updates: dict, expected_updated_at: str,
                       user_email: str = None, user_token: str = None) -> bool:
    """Update a retro item via optimistic locking."""
    return safe_update(
        "retro_items", "retro_id", retro_id, updates,
        expected_updated_at=expected_updated_at,
        user_email=user_email, user_token=user_token,
    )


def delete_retro_item(retro_id: str, user_email: str = None,
                       user_token: str = None) -> bool:
    """Soft-delete a retro item."""
    return soft_delete(
        "retro_items", "retro_id", retro_id,
        user_email=user_email, user_token=user_token,
    )


def vote_retro_item(retro_id: str, user_token: str = None) -> bool:
    """Increment votes by 1.

    Uses direct SQL for the atomic increment in production,
    and reads-then-writes in sample data mode.
    """
    from repositories.base import _use_sample_data
    if _use_sample_data():
        from models import sample_data as sd
        if "retro_items" not in sd._store:
            return False
        df = sd._store["retro_items"]
        mask = (df["retro_id"] == retro_id)
        if "is_deleted" in df.columns:
            mask = mask & (df["is_deleted"] == False)  # noqa: E712
        if mask.sum() == 0:
            return False
        df.loc[mask, "votes"] = df.loc[mask, "votes"].astype(int) + 1
        return True

    return write(
        "UPDATE retro_items SET votes = votes + 1, updated_at = current_timestamp() "
        "WHERE retro_id = :retro_id AND is_deleted = false",
        params={"retro_id": retro_id}, user_token=user_token,
    )


def convert_to_task(retro_id: str, user_token: str = None) -> bool:
    """Mark retro item status as 'converted'."""
    return safe_update(
        "retro_items", "retro_id", retro_id,
        {"status": "converted"},
        expected_updated_at=None,
        user_token=user_token,
    )
