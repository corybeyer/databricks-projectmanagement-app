"""Change History Service — field-level change tracking for entities."""

import logging
from typing import Optional
from services import audit_service

logger = logging.getLogger(__name__)


def track_update(user_email: str, entity_type: str, entity_id: str,
                 old_values: dict, new_values: dict,
                 user_token: str = None) -> None:
    """Compare old vs new values and log each changed field to audit_log.

    Args:
        user_email: Who made the change
        entity_type: e.g., "task", "project", "risk"
        entity_id: The entity's primary key
        old_values: Dict of field->value before update
        new_values: Dict of field->value after update
        user_token: OBO token for DB access
    """
    for field, new_val in new_values.items():
        old_val = old_values.get(field)
        # Convert to strings for comparison (handles None, dates, numbers)
        old_str = str(old_val) if old_val is not None else None
        new_str = str(new_val) if new_val is not None else None
        if old_str != new_str:
            audit_service.log_action(
                user_email=user_email,
                action="update",
                entity_type=entity_type,
                entity_id=entity_id,
                field_changed=field,
                old_value=old_str,
                new_value=new_str,
                user_token=user_token,
            )


def track_create(user_email: str, entity_type: str, entity_id: str,
                 details: str = None, user_token: str = None) -> None:
    """Log a create action."""
    audit_service.log_action(
        user_email=user_email, action="create",
        entity_type=entity_type, entity_id=entity_id,
        details=details, user_token=user_token,
    )


def track_delete(user_email: str, entity_type: str, entity_id: str,
                 details: str = None, user_token: str = None) -> None:
    """Log a delete action."""
    audit_service.log_action(
        user_email=user_email, action="delete",
        entity_type=entity_type, entity_id=entity_id,
        details=details, user_token=user_token,
    )


def track_approval(user_email: str, entity_type: str, entity_id: str,
                   action: str = "approve", details: str = None,
                   user_token: str = None) -> None:
    """Log an approval/rejection action (for charters, gates)."""
    audit_service.log_action(
        user_email=user_email, action=action,
        entity_type=entity_type, entity_id=entity_id,
        details=details, user_token=user_token,
    )


def get_history(entity_type: str, entity_id: str,
                user_token: str = None):
    """Get change history for display. Returns list of dicts."""
    df = audit_service.get_entity_history(entity_type, entity_id, user_token)
    if df.empty:
        return []
    return df.to_dict("records")
