"""Callback tests for projects page."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ["USE_SAMPLE_DATA"] = "true"

from unittest.mock import patch, MagicMock
import dash
from dash import Dash, html, no_update
import dash_bootstrap_components as dbc

app = Dash(__name__, use_pages=False, suppress_callback_exceptions=True,
           external_stylesheets=[dbc.themes.SLATE])

from pages.projects import (
    refresh_projects, save_project, confirm_delete_project,
    cancel_project_modal, PROJECT_FIELDS,
)


class TestRefreshProjects:
    def test_returns_content(self):
        result = refresh_projects(1, 0, None, None, None, None, None)
        assert result is not None
        assert isinstance(result, html.Div)

    def test_with_status_filter(self):
        result = refresh_projects(1, 0, None, ["active"], None, None, None)
        assert result is not None

    def test_with_health_filter(self):
        result = refresh_projects(1, 0, None, None, ["green"], None, None)
        assert result is not None

    def test_with_method_filter(self):
        result = refresh_projects(1, 0, None, None, None, ["agile"], None)
        assert result is not None

    def test_with_sort(self):
        result = refresh_projects(1, 0, None, None, None, None, "name")
        assert result is not None

    def test_with_url_search(self):
        result = refresh_projects(1, 0, "?portfolio_id=pf-001", None, None, None, None)
        assert result is not None


class TestSaveProject:
    def _num_outputs(self):
        return 6 + len(PROJECT_FIELDS) * 2

    def test_no_click_returns_no_update(self):
        result = save_project(0, None, 0, *[""] * len(PROJECT_FIELDS))
        assert all(v is no_update for v in result)
        assert len(result) == self._num_outputs()

    def test_create_valid_project(self):
        # field order: name, delivery_method, status, health, owner,
        #              start_date, target_date, budget_total, description
        fields = [
            "Test Project", "agile", "active", "green", "Test Owner",
            "2026-01-01", "2026-12-31", 100000, "A test project",
        ]
        result = save_project(1, None, 0, *fields)
        # On success: modal closes (False), counter increments, toast shows
        assert result[0] is False  # modal closes
        assert result[1] == 1  # counter incremented
        assert result[4] == "success"  # toast icon

    def test_create_missing_required_field(self):
        # Missing name (first required field)
        fields = [
            "", "agile", "active", "green", "Test Owner",
            "2026-01-01", None, None, "",
        ]
        result = save_project(1, None, 0, *fields)
        # On validation error: modal stays open (True)
        assert result[0] is True  # modal stays open
        assert result[1] is no_update  # counter unchanged
        assert result[4] == "danger"  # toast icon = error

    def test_update_existing_project(self):
        import json
        from services import project_service
        # Read current updated_at to satisfy optimistic locking
        proj_df = project_service.get_project("prj-001")
        updated_at = str(proj_df.iloc[0].get("updated_at", "")) if not proj_df.empty else ""
        stored = json.dumps({"project_id": "prj-001", "updated_at": updated_at})
        fields = [
            "Updated Name", "waterfall", "active", "green", "Owner",
            "2026-01-01", "2026-12-31", 200000, "Updated desc",
        ]
        result = save_project(1, stored, 5, *fields)
        assert result[0] is False  # modal closes
        assert result[1] == 6  # counter 5+1


class TestConfirmDeleteProject:
    def test_no_click_returns_no_update(self):
        result = confirm_delete_project(0, "prj-001", 0)
        assert all(v is no_update for v in result)

    def test_no_project_id(self):
        result = confirm_delete_project(1, None, 0)
        assert all(v is no_update for v in result)

    def test_delete_success(self):
        result = confirm_delete_project(1, "prj-001", 3)
        assert result[0] is False  # modal closes
        assert result[1] == 4  # counter 3+1
        assert result[4] == "success"


class TestCancelProjectModal:
    def test_returns_false(self):
        result = cancel_project_modal(1)
        assert result is False
