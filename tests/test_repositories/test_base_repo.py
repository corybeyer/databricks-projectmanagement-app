"""Tests for base repository infrastructure."""
import os
os.environ["USE_SAMPLE_DATA"] = "true"

import pytest
from repositories.base import _validate_identifier, ALLOWED_TABLES, ALLOWED_ID_COLUMNS


class TestValidateIdentifier:
    def test_valid_table(self):
        # Should not raise
        _validate_identifier("tasks", ALLOWED_TABLES, "table")

    def test_invalid_table(self):
        with pytest.raises(ValueError):
            _validate_identifier("not_a_table", ALLOWED_TABLES, "table")

    def test_valid_id_column(self):
        _validate_identifier("task_id", ALLOWED_ID_COLUMNS, "id_column")

    def test_invalid_id_column(self):
        with pytest.raises(ValueError):
            _validate_identifier("evil_column", ALLOWED_ID_COLUMNS, "id_column")

    def test_all_tables_valid(self):
        """Every expected table is in the allowlist."""
        expected_tables = {
            "tasks", "sprints", "projects", "portfolios", "risks",
            "project_charters", "phases", "gates", "deliverables",
            "comments", "time_entries", "team_members", "retro_items",
            "dependencies", "departments", "project_team", "audit_log",
            "status_transitions",
        }
        for table in expected_tables:
            _validate_identifier(table, ALLOWED_TABLES, "table")

    def test_all_id_columns_valid(self):
        """Every expected ID column is in the allowlist."""
        expected_ids = {
            "task_id", "sprint_id", "project_id", "portfolio_id", "risk_id",
            "charter_id", "phase_id", "gate_id", "deliverable_id",
            "comment_id", "entry_id", "user_id", "retro_id",
            "dependency_id", "department_id", "audit_id",
        }
        for col in expected_ids:
            _validate_identifier(col, ALLOWED_ID_COLUMNS, "id_column")

    def test_sql_injection_attempt(self):
        with pytest.raises(ValueError):
            _validate_identifier("tasks; DROP TABLE tasks", ALLOWED_TABLES, "table")

    def test_empty_string(self):
        with pytest.raises(ValueError):
            _validate_identifier("", ALLOWED_TABLES, "table")
