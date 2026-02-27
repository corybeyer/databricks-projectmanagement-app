"""Notification Service — user notification management."""

import uuid
import logging

logger = logging.getLogger(__name__)


def notify(user_email: str, notification_type: str, title: str,
           message: str, entity_type: str = None, entity_id: str = None) -> bool:
    """Create a notification for a user.

    Args:
        user_email: Recipient email
        notification_type: task_assignment | charter_approved | gate_decision |
                          risk_escalation | sprint_closed | comment_added
        title: Short notification title
        message: Full notification message
        entity_type: Related entity type (task, charter, risk, etc.)
        entity_id: Related entity ID
    """
    from repositories.notification_repo import create_notification

    record = {
        "notification_id": str(uuid.uuid4()),
        "user_email": user_email,
        "notification_type": notification_type,
        "title": title,
        "message": message,
        "entity_type": entity_type or "",
        "entity_id": entity_id or "",
        "is_read": False,
    }

    try:
        return create_notification(record)
    except Exception as e:
        logger.error("Failed to create notification: %s", e)
        return False


def get_unread(user_email: str) -> list:
    """Get unread notifications for a user as list of dicts."""
    from repositories.notification_repo import get_unread_notifications

    df = get_unread_notifications(user_email)
    if df.empty:
        return []
    return df.to_dict("records")


def get_unread_count(user_email: str) -> int:
    """Get count of unread notifications."""
    from repositories.notification_repo import get_unread_count as _get_count
    return _get_count(user_email)


def get_all(user_email: str) -> list:
    """Get all notifications for a user as list of dicts."""
    from repositories.notification_repo import get_notifications

    df = get_notifications(user_email)
    if df.empty:
        return []
    return df.to_dict("records")


def mark_read(notification_id: str) -> bool:
    """Mark a notification as read."""
    from repositories.notification_repo import mark_as_read
    return mark_as_read(notification_id)


def mark_all_read(user_email: str) -> bool:
    """Mark all notifications as read for a user."""
    from repositories.notification_repo import mark_all_read as _mark_all
    return _mark_all(user_email)
