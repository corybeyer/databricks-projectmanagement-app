"""Tests for task repository against sample data."""
import os
os.environ["USE_SAMPLE_DATA"] = "true"

import pandas as pd


class TestTaskRepo:
    def test_get_all_tasks(self):
        from repositories.task_repo import get_all_tasks
        df = get_all_tasks()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert "task_id" in df.columns
        assert "title" in df.columns

    def test_get_backlog(self):
        from repositories.task_repo import get_backlog
        df = get_backlog("prj-001")
        assert isinstance(df, pd.DataFrame)

    def test_get_task_by_id(self):
        from repositories.task_repo import get_task_by_id
        df = get_task_by_id("t-001")
        assert isinstance(df, pd.DataFrame)

    def test_create_task(self):
        from repositories.task_repo import create_task, get_all_tasks
        result = create_task({
            "task_id": "t-test-001",
            "title": "Test Task",
            "task_type": "story",
            "status": "todo",
            "priority": "medium",
            "story_points": 3,
            "sprint_id": "sp-001",
            "project_id": "prj-001",
            "created_by": "test@pm-hub.local",
        })
        assert result is True
        df = get_all_tasks()
        assert "t-test-001" in df["task_id"].values

    def test_update_task(self):
        from repositories.task_repo import update_task
        result = update_task(
            "t-001", {"title": "Updated Title"}, expected_updated_at=None,
            user_email="test@pm-hub.local",
        )
        assert isinstance(result, bool)

    def test_delete_task(self):
        from repositories.task_repo import delete_task, get_all_tasks
        result = delete_task("t-001", user_email="test@pm-hub.local")
        assert result is True
        # After deletion, task should not appear in non-deleted results
        df = get_all_tasks()
        if not df.empty:
            deleted = df[df["task_id"] == "t-001"]
            # Either missing or marked as deleted
            assert deleted.empty or deleted.iloc[0].get("is_deleted", False)

    def test_update_task_status(self):
        from repositories.task_repo import update_task_status
        result = update_task_status("t-001", "in_progress", "test@pm-hub.local")
        assert isinstance(result, bool)

    def test_move_task_to_sprint(self):
        from repositories.task_repo import move_task_to_sprint
        result = move_task_to_sprint("t-001", "sp-002")
        assert isinstance(result, bool)
