"""Audit Service — action logging (placeholder)."""

import logging

logger = logging.getLogger(__name__)


def log_action(user_email: str, action: str, entity_type: str,
               entity_id: str, details: str = None):
    """Log an audit event. Placeholder — writes to log only."""
    logger.info("AUDIT: user=%s action=%s entity=%s/%s details=%s",
                user_email, action, entity_type, entity_id, details)
