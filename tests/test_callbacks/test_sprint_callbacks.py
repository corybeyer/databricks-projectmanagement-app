"""Callback tests for sprint page."""

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

from pages.sprint import (
    populate_sprint_selector, refresh_sprint, save_task,
    confirm_delete_task, cancel_task_modal, save_sprint,
    close_current_sprint, TASK_FIELDS, SPRINT_FIELDS,
)


class TestPopulateSprintSelector:
    def test_returns_options_and_value(self):
        options, value = populate_sprint_selector(1, None)
        assert isinstance(options, list)
        assert len(options) > 0
        assert value is not None

    def test_with_project_id(self):
        options, value = populate_sprint_selector(1, "prj-001")
        assert isinstance(options, list)


class TestRefreshSprint:
    def test_returns_content(self):
        result = refresh_sprint(1, 0, None, None)
        assert result is not None
        assert isinstance(result, html.Div)

    def test_with_sprint_id(self):
        result = refresh_sprint(1, 0, "sp-004", None)
        assert result is not None

    def test_with_project_id(self):
        result = refresh_sprint(1, 0, None, "prj-001")
        assert result is not None


class TestSaveTask:
    def _num_outputs(self):
        return 6 + len(TASK_FIELDS) * 2

    def test_no_click_returns_no_update(self):
        result = save_task(0, None, "sp-004", 0, None, *[""] * len(TASK_FIELDS))
        assert all(v is no_update for v in result)
        assert len(result) == self._num_outputs()

    def test_create_valid_task(self):
        # field order: title, task_type, priority, story_points, assignee, description
        fields = ["Test Task", "story", "medium", 5, "u-001", "A test task"]
        result = save_task(1, None, "sp-004", 0, None, *fields)
        assert result[0] is False  # modal closes
        assert result[1] == 1  # counter incremented
        assert result[4] == "success"

    def test_create_missing_title(self):
        fields = ["", "story", "medium", 5, None, ""]
        result = save_task(1, None, "sp-004", 0, None, *fields)
        assert result[0] is True  # modal stays open
        assert result[1] is no_update
        assert result[4] == "danger"


class TestConfirmDeleteTask:
    def test_no_task_id(self):
        result = confirm_delete_task(1, None, 0)
        assert all(v is no_update for v in result)

    def test_delete_success(self):
        # Use an existing sample data task ID
        result = confirm_delete_task(1, "t-001", 2)
        assert result[0] is False  # modal closes
        assert result[1] == 3  # counter 2+1
        assert result[4] == "success"


class TestCancelTaskModal:
    def test_returns_false(self):
        result = cancel_task_modal(1)
        assert result is False


class TestSaveSprint:
    def _num_outputs(self):
        return 6 + len(SPRINT_FIELDS) * 2

    def test_no_click_returns_no_update(self):
        result = save_sprint(0, 0, None, *[""] * len(SPRINT_FIELDS))
        assert all(v is no_update for v in result)
        assert len(result) == self._num_outputs()

    def test_create_valid_sprint(self):
        # field order: name, goal, start_date, end_date, capacity_points
        fields = ["Sprint 99", "Test goal", "2026-03-01", "2026-03-14", 40]
        result = save_sprint(1, 0, None, *fields)
        assert result[0] is False  # modal closes
        assert result[1] == 1  # counter incremented
        assert result[4] == "success"

    def test_create_missing_name(self):
        fields = ["", "", "2026-03-01", "2026-03-14", 40]
        result = save_sprint(1, 0, None, *fields)
        assert result[0] is True  # modal stays open
        assert result[1] is no_update
        assert result[4] == "danger"


class TestCloseCurrentSprint:
    def test_no_sprint_selected(self):
        result = close_current_sprint(1, None, 0)
        # Returns error toast
        assert result[0] is no_update
        assert "No sprint" in str(result[1])

    def test_close_active_sprint(self):
        result = close_current_sprint(1, "sp-004", 5)
        # Should succeed
        assert result[0] == 6  # counter 5+1
        assert result[3] == "success"
