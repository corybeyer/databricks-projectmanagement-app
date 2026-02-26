"""Notification Service — user notifications (placeholder)."""

import logging

logger = logging.getLogger(__name__)


def notify(user_email: str, notification_type: str, title: str,
           message: str, entity_type: str = None, entity_id: str = None):
    """Send a notification. Placeholder — logs only."""
    logger.info("NOTIFY: to=%s type=%s title=%s", user_email, notification_type, title)


def get_unread(user_email: str) -> list:
    """Get unread notifications. Placeholder — returns empty list."""
    return []


def mark_read(notification_id: str) -> bool:
    """Mark a notification as read. Placeholder."""
    return True
