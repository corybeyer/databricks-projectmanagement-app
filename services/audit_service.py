"""Audit Service — centralized action logging."""

import logging
import uuid
from typing import Optional
import pandas as pd
from repositories import audit_repo

logger = logging.getLogger(__name__)


def log_action(user_email: str, action: str, entity_type: str,
               entity_id: str, details: str = None,
               field_changed: str = None, old_value: str = None,
               new_value: str = None, user_token: str = None) -> bool:
    """Log an audit event to the audit_log table."""
    audit_id = str(uuid.uuid4())
    logger.info("AUDIT: user=%s action=%s entity=%s/%s",
                user_email, action, entity_type, entity_id)
    return audit_repo.log_audit_entry(
        audit_id=audit_id, user_email=user_email, action=action,
        entity_type=entity_type, entity_id=entity_id,
        field_changed=field_changed, old_value=old_value,
        new_value=new_value, details=details, user_token=user_token,
    )


def get_entity_history(entity_type: str, entity_id: str,
                       user_token: str = None) -> pd.DataFrame:
    """Get change history for a specific entity."""
    return audit_repo.get_audit_log(
        entity_type=entity_type, entity_id=entity_id, user_token=user_token)


def get_user_activity(user_email: str, user_token: str = None) -> pd.DataFrame:
    """Get recent activity for a user."""
    return audit_repo.get_user_activity(user_email, user_token=user_token)
