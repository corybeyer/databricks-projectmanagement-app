"""
Application Settings — Environment-driven configuration
========================================================
Uses Pydantic BaseSettings to read from .env locally
and app.yaml env vars in Databricks.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Databricks
    databricks_host: Optional[str] = None
    databricks_sql_warehouse_id: Optional[str] = None

    # App
    app_env: str = "development"
    app_port: int = 8050
    use_sample_data: bool = True
    debug: bool = False

    # Unity Catalog
    uc_catalog: str = "workspace"
    uc_schema: str = "project_management"

    # Feature flags
    feature_portfolios: bool = True
    feature_roadmap: bool = False
    feature_gantt: bool = False
    feature_sprint: bool = False
    feature_my_work: bool = False
    feature_backlog: bool = False
    feature_retros: bool = False
    feature_reports: bool = False
    feature_resources: bool = False
    feature_risks: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_local(self) -> bool:
        return self.app_env == "development"
