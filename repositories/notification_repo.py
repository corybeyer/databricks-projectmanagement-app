"""Notification Repository — notification data access."""

import logging
import pandas as pd
from repositories.base import query, write, soft_delete

logger = logging.getLogger(__name__)


def get_notifications(user_email: str = None) -> pd.DataFrame:
    """Get notifications, optionally filtered by user email."""
    def _sample():
        from models.sample_data import get_notifications as _get
        return _get()

    sql_str = """
        SELECT * FROM notifications
        WHERE is_deleted = false
    """
    params = {}
    if user_email:
        sql_str += " AND user_email = :user_email"
        params["user_email"] = user_email
    sql_str += " ORDER BY created_at DESC"

    df = query(sql_str, params=params, sample_fallback=_sample)
    if user_email and not df.empty and "user_email" in df.columns:
        df = df[df["user_email"] == user_email]
    return df


def get_unread_notifications(user_email: str) -> pd.DataFrame:
    """Get unread notifications for a user."""
    df = get_notifications(user_email)
    if not df.empty and "is_read" in df.columns:
        df = df[df["is_read"] == False]  # noqa: E712
    return df


def get_unread_count(user_email: str) -> int:
    """Get count of unread notifications for a user."""
    return len(get_unread_notifications(user_email))


def create_notification(record: dict) -> bool:
    """Create a new notification."""
    sql_str = """
        INSERT INTO notifications
        (notification_id, user_email, notification_type, title, message,
         entity_type, entity_id, is_read, created_at)
        VALUES (:notification_id, :user_email, :notification_type, :title,
                :message, :entity_type, :entity_id, false, current_timestamp())
    """
    return write(sql_str, params=record, table_name="notifications", record=record)


def mark_as_read(notification_id: str, user_email: str = None) -> bool:
    """Mark a notification as read."""
    from repositories.base import safe_update
    return safe_update(
        "notifications", "notification_id", notification_id,
        {"is_read": True}, expected_updated_at=None,
        user_email=user_email,
    )


def mark_all_read(user_email: str) -> bool:
    """Mark all notifications as read for a user."""
    df = get_unread_notifications(user_email)
    if df.empty:
        return True
    for _, row in df.iterrows():
        mark_as_read(row["notification_id"], user_email=user_email)
    return True


def delete_notification(notification_id: str, user_email: str = None) -> bool:
    """Soft delete a notification."""
    return soft_delete("notifications", "notification_id", notification_id,
                       user_email=user_email)
