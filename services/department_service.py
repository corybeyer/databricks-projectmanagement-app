"""Department Service — organizational hierarchy logic."""

import logging
from typing import Optional
import pandas as pd
from repositories import department_repo
from services.auth_service import get_current_user

logger = logging.getLogger(__name__)


def get_departments(user_token: str = None) -> pd.DataFrame:
    """Get all active departments."""
    return department_repo.get_departments(user_token=user_token)


def get_department(department_id: str, user_token: str = None) -> pd.DataFrame:
    """Get a single department by ID."""
    return department_repo.get_department(department_id, user_token=user_token)


def get_department_hierarchy(user_token: str = None) -> pd.DataFrame:
    """Get departments with portfolio and member counts."""
    return department_repo.get_department_hierarchy(user_token=user_token)


def get_user_department(user_token: str = None) -> Optional[str]:
    """Get the current user's department_id. Returns None in local dev."""
    user = get_current_user()
    # Placeholder: return None (all departments visible)
    # When RBAC enforced, look up user's department from team_members
    return None
