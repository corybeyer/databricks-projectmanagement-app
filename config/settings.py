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
    log_level: str = "INFO"

    # Unity Catalog
    uc_catalog: str = "workspace"
    uc_schema: str = "project_management"

    # Feature flags
    feature_portfolios: bool = True
    feature_roadmap: bool = True
    feature_gantt: bool = True
    feature_sprint: bool = True
    feature_my_work: bool = True
    feature_backlog: bool = True
    feature_retros: bool = True
    feature_reports: bool = True
    feature_resources: bool = True
    feature_risks: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_local(self) -> bool:
        return self.app_env == "development"
