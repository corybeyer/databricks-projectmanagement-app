"""
Auth Service — User identity and permissions
==============================================
Placeholder pattern: has_permission() returns True.
Switch to real enforcement by changing one function.
"""

import logging
from typing import Optional
from db.unity_catalog import get_user_token as _get_token, get_user_email as _get_email

logger = logging.getLogger(__name__)


def get_user_token() -> Optional[str]:
    """Get the current user's OBO token. None in local dev."""
    return _get_token()


def get_user_email() -> Optional[str]:
    """Get the current user's email. None in local dev."""
    return _get_email()


def get_current_user() -> dict:
    """Get current user info from Databricks Apps headers."""
    return {
        "email": get_user_email() or "local-dev@pm-hub.local",
        "token": get_user_token(),
    }


def has_permission(user: dict, required_level: str = "viewer") -> bool:
    """Check if user has required permission level. Returns True (placeholder)."""
    return True


def require_role(required_level: str = "viewer"):
    """Page-level guard. Returns None if allowed, error component if denied."""
    user = get_current_user()
    if not has_permission(user, required_level):
        return None  # Would return error component when enforced
    return None
