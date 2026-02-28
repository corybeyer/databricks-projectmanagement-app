"""
Auth Service — User identity and permissions (RBAC)
====================================================
Role-based access control with department scoping.
Roles: admin (100), lead/pm (80), engineer (50), viewer (20).
"""

import logging
from typing import Optional
from repositories.auth_repo import get_current_user_token as _get_token, get_current_user_email as _get_email

logger = logging.getLogger(__name__)

# Role permission levels
ROLE_LEVELS = {
    "admin": 100,
    "lead": 80,
    "pm": 80,
    "engineer": 50,
    "viewer": 20,
}

# Required permission level for operations
OPERATION_LEVELS = {
    "read": 20,       # viewer+
    "comment": 50,    # engineer+
    "create": 50,     # engineer+
    "update": 50,     # engineer+
    "delete": 80,     # lead/pm+
    "approve": 80,    # lead/pm+
    "admin": 100,     # admin only
}

# Entity-specific overrides: engineers can only CRUD these entities
ENGINEER_ALLOWED_ENTITIES = {"task", "comment", "time_entry", "retro_item"}


def get_user_token() -> Optional[str]:
    """Get the current user's OBO token. None in local dev."""
    return _get_token()


def get_user_email() -> Optional[str]:
    """Get the current user's email. None in local dev."""
    return _get_email()


def get_current_user() -> dict:
    """Get current user info. In local dev, returns admin for convenience."""
    email = get_user_email() or "local-dev@pm-hub.local"
    role = _get_user_role(email)
    return {
        "email": email,
        "token": get_user_token(),
        "role": role,
        "department_id": _get_user_department(email),
    }


def _get_user_role(email: str) -> str:
    """Look up user role from team_members table. Falls back to 'viewer'."""
    try:
        from repositories.resource_repo import get_team_members
        members = get_team_members()
        if not members.empty:
            user_row = members[members["email"] == email]
            if not user_row.empty and "role" in user_row.columns:
                return user_row.iloc[0]["role"]
    except Exception:
        pass
    # Local dev default
    if email == "local-dev@pm-hub.local":
        return "admin"
    return "viewer"


def _get_user_department(email: str) -> Optional[str]:
    """Look up user's department from team_members table."""
    try:
        from repositories.resource_repo import get_team_members
        members = get_team_members()
        if not members.empty:
            user_row = members[members["email"] == email]
            if not user_row.empty and "department_id" in user_row.columns:
                return user_row.iloc[0]["department_id"]
    except Exception:
        pass
    return None


def has_permission(user: dict, operation: str = "read", entity_type: str = None) -> bool:
    """Check if user has permission for an operation.

    Args:
        user: User dict with 'role' key
        operation: One of OPERATION_LEVELS keys
        entity_type: Optional entity for engineer-level restrictions
    Returns:
        True if allowed
    """
    role = user.get("role", "viewer")
    role_level = ROLE_LEVELS.get(role, 20)
    required_level = OPERATION_LEVELS.get(operation, 100)

    # Admin bypasses all checks
    if role_level >= 100:
        return True

    # Basic level check
    if role_level < required_level:
        return False

    # Engineer entity restriction
    if role == "engineer" and entity_type and operation in ("create", "update", "delete"):
        if entity_type not in ENGINEER_ALLOWED_ENTITIES:
            return False

    return True


def get_department_filter(user: dict) -> Optional[str]:
    """Return department_id to filter by, or None if user sees all.

    Admins see all departments. Other roles see only their own.
    """
    if user.get("role") == "admin":
        return None
    return user.get("department_id")


def can_access_department(user: dict, department_id: str) -> bool:
    """Check if user can access data from a specific department."""
    if user.get("role") == "admin":
        return True
    return user.get("department_id") == department_id


def require_role(required_level: str = "viewer"):
    """Page-level guard. Returns None if allowed, error message if denied."""
    user = get_current_user()
    if not has_permission(user, required_level):
        return f"Access denied. Required role: {required_level}"
    return None
