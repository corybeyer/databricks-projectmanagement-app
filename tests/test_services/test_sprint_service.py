"""Tests for sprint service."""
import os
os.environ["USE_SAMPLE_DATA"] = "true"

from services.sprint_service import (
    create_sprint_from_form, close_sprint, get_sprints, get_sprint,
    get_sprint_tasks,
)


class TestCreateSprint:
    def test_create_valid_sprint(self):
        result = create_sprint_from_form({
            "name": "Sprint 99",
            "start_date": "2026-03-01",
            "end_date": "2026-03-14",
            "capacity_points": "40",
            "goal": "Deliver feature X",
            "project_id": "prj-001",
        }, user_email="test@pm-hub.local")
        assert result["success"] is True
        assert "created" in result["message"].lower()

    def test_create_sprint_missing_name(self):
        result = create_sprint_from_form({
            "name": "",
            "start_date": "2026-03-01",
            "end_date": "2026-03-14",
        }, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_sprint_missing_dates(self):
        result = create_sprint_from_form({
            "name": "Sprint X",
            "start_date": None,
            "end_date": None,
        }, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_sprint_end_before_start(self):
        result = create_sprint_from_form({
            "name": "Sprint Bad Dates",
            "start_date": "2026-03-14",
            "end_date": "2026-03-01",
        }, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_sprint_invalid_date_format(self):
        result = create_sprint_from_form({
            "name": "Sprint Bad",
            "start_date": "not-a-date",
            "end_date": "2026-03-14",
        }, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_sprint_with_capacity(self):
        result = create_sprint_from_form({
            "name": "Sprint Cap",
            "start_date": "2026-04-01",
            "end_date": "2026-04-14",
            "capacity_points": "60",
        }, user_email="test@pm-hub.local")
        assert result["success"] is True


class TestGetSprints:
    def test_get_sprints_returns_dataframe(self):
        df = get_sprints("prj-001")
        assert df is not None
        assert hasattr(df, "columns")

    def test_get_sprint_by_id(self):
        df = get_sprint("sp-001")
        assert df is not None

    def test_get_sprint_tasks(self):
        df = get_sprint_tasks("sp-001")
        assert df is not None
        assert hasattr(df, "columns")


class TestCloseSprint:
    def test_close_sprint(self):
        result = close_sprint("sp-001", user_email="test@pm-hub.local")
        assert "success" in result
        assert isinstance(result["success"], bool)
