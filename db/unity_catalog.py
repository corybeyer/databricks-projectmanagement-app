"""
Unity Catalog Connection — OBO Auth
====================================
Per-user SQL queries via databricks-sql-connector.
Uses X-Forwarded-Access-Token for on-behalf-of authentication.
"""

import os
import logging
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)


def get_user_token() -> Optional[str]:
    """Get the user's OAuth token from Databricks Apps headers."""
    try:
        from flask import request
        return request.headers.get("X-Forwarded-Access-Token")
    except RuntimeError:
        return None


def get_user_email() -> Optional[str]:
    """Get the user's email from Databricks Apps headers."""
    try:
        from flask import request
        return request.headers.get("X-Forwarded-Email")
    except RuntimeError:
        return None


def get_connection(user_token: str):
    """Create a SQL connection using the user's OAuth token."""
    from databricks import sql
    from databricks.sdk.core import Config

    cfg = Config()
    warehouse_id = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID")

    return sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{warehouse_id}",
        access_token=user_token,
    )


def execute_query(sql_str: str, params: dict = None, user_token: str = None) -> pd.DataFrame:
    """Execute a parameterized read query. Returns empty DataFrame on failure."""
    if user_token is None:
        return None  # Caller should fall back to sample data

    try:
        with get_connection(user_token) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_str, parameters=params)
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    return pd.DataFrame(rows, columns=columns)
                return pd.DataFrame()
    except Exception as e:
        logger.error("Query error: %s", e)
        return pd.DataFrame()


def execute_write(sql_str: str, params: dict = None, user_token: str = None) -> bool:
    """Execute a parameterized write operation. Returns True on success."""
    if user_token is None:
        logger.warning("Write skipped — no database connection (local dev)")
        return False

    try:
        with get_connection(user_token) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_str, parameters=params)
        return True
    except Exception as e:
        logger.error("Write error: %s", e)
        return False
