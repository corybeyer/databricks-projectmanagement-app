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

    if not warehouse_id:
        raise ConnectionError("DATABRICKS_SQL_WAREHOUSE_ID not configured")

    return sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{warehouse_id}",
        access_token=user_token,
    )


def execute_query(sql_str: str, params: dict = None, user_token: str = None) -> pd.DataFrame:
    """Execute a parameterized read query. Returns empty DataFrame on failure.

    Handles specific Databricks SQL exceptions:
    - ServerOperationError: Query execution failures (bad SQL, permission denied)
    - OperationalError: Connection issues (warehouse stopped, network)
    - DatabaseError: General DB errors
    """
    if user_token is None:
        return None  # Caller should fall back to sample data

    try:
        from databricks.sql.exc import (
            ServerOperationError,
            OperationalError,
            DatabaseError,
        )
    except ImportError:
        ServerOperationError = OperationalError = DatabaseError = Exception

    try:
        with get_connection(user_token) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_str, parameters=params)
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    result = cursor.fetchall_arrow()
                    return result.to_pandas()
                return pd.DataFrame()
    except ServerOperationError as e:
        logger.error("SQL execution error: %s", e)
        return pd.DataFrame()
    except OperationalError as e:
        logger.error("Database connection error (warehouse may be stopped): %s", e)
        return pd.DataFrame()
    except DatabaseError as e:
        logger.error("Database error: %s", e)
        return pd.DataFrame()
    except ConnectionError as e:
        logger.error("Connection configuration error: %s", e)
        return pd.DataFrame()


def execute_write(sql_str: str, params: dict = None, user_token: str = None) -> bool:
    """Execute a parameterized write operation. Returns True on success.

    Handles specific Databricks SQL exceptions for write operations.
    """
    if user_token is None:
        logger.warning("Write skipped — no database connection (local dev)")
        return False

    try:
        from databricks.sql.exc import (
            ServerOperationError,
            OperationalError,
            DatabaseError,
        )
    except ImportError:
        ServerOperationError = OperationalError = DatabaseError = Exception

    try:
        with get_connection(user_token) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_str, parameters=params)
        return True
    except ServerOperationError as e:
        logger.error("SQL write execution error: %s", e)
        return False
    except OperationalError as e:
        logger.error("Database connection error on write: %s", e)
        return False
    except DatabaseError as e:
        logger.error("Database write error: %s", e)
        return False
    except ConnectionError as e:
        logger.error("Connection configuration error: %s", e)
        return False
