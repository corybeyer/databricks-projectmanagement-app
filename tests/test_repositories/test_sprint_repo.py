"""Tests for sprint repository against sample data."""
import os
os.environ["USE_SAMPLE_DATA"] = "true"

import pandas as pd


class TestSprintRepo:
    def test_get_sprints(self):
        from repositories.sprint_repo import get_sprints
        df = get_sprints("prj-001")
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert "sprint_id" in df.columns

    def test_get_sprint_tasks(self):
        from repositories.sprint_repo import get_sprint_tasks
        df = get_sprint_tasks("sp-001")
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert "task_id" in df.columns

    def test_get_sprint_by_id(self):
        from repositories.sprint_repo import get_sprint_by_id
        df = get_sprint_by_id("sp-001")
        assert isinstance(df, pd.DataFrame)

    def test_create_sprint(self):
        from repositories.sprint_repo import create_sprint, get_sprints
        result = create_sprint({
            "sprint_id": "sp-test-001",
            "name": "Test Sprint",
            "project_id": "prj-001",
            "status": "planning",
            "start_date": "2026-04-01",
            "end_date": "2026-04-14",
            "created_by": "test@pm-hub.local",
        })
        assert result is True
        df = get_sprints("prj-001")
        assert "sp-test-001" in df["sprint_id"].values

    def test_close_sprint(self):
        from repositories.sprint_repo import close_sprint
        result = close_sprint("sp-001", user_email="test@pm-hub.local")
        assert isinstance(result, bool)

    def test_update_sprint(self):
        from repositories.sprint_repo import update_sprint
        result = update_sprint(
            "sp-001", {"name": "Renamed Sprint"},
            expected_updated_at=None,
            user_email="test@pm-hub.local",
        )
        assert isinstance(result, bool)
