"""Callback tests for backlog page."""

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

from pages.backlog import (
    refresh_backlog, save_task, confirm_delete, cancel_task_modal,
    TASK_FIELDS,
)


class TestRefreshBacklog:
    def test_returns_content(self):
        result = refresh_backlog(1, 0, None, None, None, None, None)
        assert result is not None
        assert isinstance(result, html.Div)

    def test_with_project_id(self):
        result = refresh_backlog(1, 0, "prj-001", None, None, None, None)
        assert result is not None

    def test_with_status_filter(self):
        result = refresh_backlog(1, 0, None, ["backlog"], None, None, None)
        assert result is not None

    def test_with_priority_filter(self):
        result = refresh_backlog(1, 0, None, None, ["high"], None, None)
        assert result is not None

    def test_with_assignee_filter(self):
        result = refresh_backlog(1, 0, None, None, None, ["u-001"], None)
        assert result is not None

    def test_with_type_filter(self):
        result = refresh_backlog(1, 0, None, None, None, None, ["story"])
        assert result is not None


class TestSaveTask:
    def _num_outputs(self):
        return 6 + len(TASK_FIELDS) * 2

    def test_no_click_returns_no_update(self):
        result = save_task(0, None, 0, None, *[""] * len(TASK_FIELDS))
        assert all(v is no_update for v in result)
        assert len(result) == self._num_outputs()

    def test_create_valid_task(self):
        # field order: title, task_type, priority, story_points, assignee, description
        fields = ["Backlog Task", "story", "medium", 3, "u-001", "A backlog task"]
        result = save_task(1, None, 0, None, *fields)
        assert result[0] is False  # modal closes
        assert result[1] == 1  # counter incremented
        assert result[4] == "success"

    def test_create_missing_title(self):
        fields = ["", "story", "medium", 3, None, ""]
        result = save_task(1, None, 0, None, *fields)
        assert result[0] is True  # modal stays open
        assert result[1] is no_update
        assert result[4] == "danger"

    def test_update_existing_task(self):
        import json
        from services import task_service
        # Read current updated_at to satisfy optimistic locking
        task_df = task_service.get_task("t-001")
        updated_at = str(task_df.iloc[0].get("updated_at", "")) if not task_df.empty else ""
        stored = json.dumps({"task_id": "t-001", "updated_at": updated_at})
        fields = ["Updated Task", "bug", "high", 8, "u-002", "Updated desc"]
        result = save_task(1, stored, 3, None, *fields)
        assert result[0] is False  # modal closes
        assert result[1] == 4  # counter 3+1

    def test_with_active_project(self):
        fields = ["Project Task", "task", "low", 2, None, ""]
        result = save_task(1, None, 0, "prj-001", *fields)
        assert result[0] is False
        assert result[4] == "success"


class TestConfirmDelete:
    def test_no_click_returns_no_update(self):
        result = confirm_delete(0, "t-001", 0)
        assert all(v is no_update for v in result)

    def test_no_task_id(self):
        result = confirm_delete(1, None, 0)
        assert all(v is no_update for v in result)

    def test_delete_success(self):
        result = confirm_delete(1, "t-001", 2)
        assert result[0] is False  # modal closes
        assert result[1] == 3  # counter 2+1
        assert result[4] == "success"


class TestCancelTaskModal:
    def test_returns_false(self):
        result = cancel_task_modal(1)
        assert result is False
