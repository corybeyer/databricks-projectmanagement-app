"""Audit Repository — audit log queries and writes."""

import pandas as pd
from repositories.base import query, write
from models import sample_data


def log_audit_entry(audit_id: str, user_email: str, action: str,
                    entity_type: str, entity_id: str,
                    field_changed: str = None, old_value: str = None,
                    new_value: str = None, details: str = None,
                    user_token: str = None) -> bool:
    """Write an audit log entry."""
    return write("""
        INSERT INTO audit_log (audit_id, user_email, action, entity_type,
                               entity_id, field_changed, old_value, new_value, details)
        VALUES (:audit_id, :user_email, :action, :entity_type,
                :entity_id, :field_changed, :old_value, :new_value, :details)
    """, params={
        "audit_id": audit_id, "user_email": user_email, "action": action,
        "entity_type": entity_type, "entity_id": entity_id,
        "field_changed": field_changed, "old_value": old_value,
        "new_value": new_value, "details": details,
    }, user_token=user_token)


def get_audit_log(entity_type: str = None, entity_id: str = None,
                  limit: int = 100, user_token: str = None) -> pd.DataFrame:
    """Get audit log entries, optionally filtered by entity."""
    if entity_type and entity_id:
        return query("""
            SELECT * FROM audit_log
            WHERE entity_type = :entity_type AND entity_id = :entity_id
            ORDER BY created_at DESC
            LIMIT :limit
        """, params={"entity_type": entity_type, "entity_id": entity_id,
                     "limit": limit}, user_token=user_token,
            sample_fallback=sample_data.get_audit_log)

    return query("""
        SELECT * FROM audit_log
        ORDER BY created_at DESC
        LIMIT :limit
    """, params={"limit": limit}, user_token=user_token,
        sample_fallback=sample_data.get_audit_log)


def get_user_activity(user_email: str, limit: int = 50,
                      user_token: str = None) -> pd.DataFrame:
    """Get recent activity for a specific user."""
    return query("""
        SELECT * FROM audit_log
        WHERE user_email = :user_email
        ORDER BY created_at DESC
        LIMIT :limit
    """, params={"user_email": user_email, "limit": limit},
        user_token=user_token, sample_fallback=sample_data.get_audit_log)
