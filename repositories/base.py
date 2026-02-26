"""
Repository Base — Shared query infrastructure
===============================================
All domain repositories inherit query helpers from here.
Handles sample data fallback, optimistic locking, soft deletes.
"""

import logging
from typing import Optional
import pandas as pd
from db.unity_catalog import execute_query, execute_write

logger = logging.getLogger(__name__)


def query(sql_str: str, params: dict = None, user_token: str = None,
          sample_fallback=None) -> pd.DataFrame:
    """Execute a read query with sample data fallback for local dev."""
    result = execute_query(sql_str, params=params, user_token=user_token)
    if result is None and sample_fallback is not None:
        return sample_fallback()
    return result if result is not None else pd.DataFrame()


def write(sql_str: str, params: dict = None, user_token: str = None) -> bool:
    """Execute a write operation."""
    return execute_write(sql_str, params=params, user_token=user_token)


def safe_update(table: str, id_column: str, id_value: str,
                updates: dict, expected_updated_at: str,
                user_token: str = None) -> bool:
    """Optimistic locking update — fails if record was modified since last read."""
    set_clauses = ", ".join(f"{col} = :{col}" for col in updates)
    sql_str = (
        f"UPDATE {table} SET {set_clauses}, updated_at = current_timestamp() "
        f"WHERE {id_column} = :_id AND updated_at = :_expected_updated_at"
    )
    params = {**updates, "_id": id_value, "_expected_updated_at": expected_updated_at}
    return write(sql_str, params=params, user_token=user_token)
