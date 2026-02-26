"""Charter Repository — project charter queries."""

import pandas as pd
from repositories.base import query
from models import sample_data


def get_project_charter(project_id: str, user_token: str = None) -> pd.DataFrame:
    return query("""
        SELECT c.*
        FROM project_charters c
        WHERE c.project_id = :project_id
          AND c.is_deleted = false
    """, params={"project_id": project_id}, user_token=user_token,
        sample_fallback=sample_data.get_project_charter)
