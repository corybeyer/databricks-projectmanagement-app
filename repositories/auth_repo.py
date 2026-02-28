"""Authentication Repository — wraps db-layer identity functions."""

from typing import Optional
from db.unity_catalog import get_user_token, get_user_email


def get_current_user_token() -> Optional[str]:
    """Get the current user's OBO token. None in local dev."""
    return get_user_token()


def get_current_user_email() -> Optional[str]:
    """Get the current user's email. None in local dev."""
    return get_user_email()
