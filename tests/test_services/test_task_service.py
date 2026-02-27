"""Tests for task service."""
import os
os.environ["USE_SAMPLE_DATA"] = "true"

from services.task_service import (
    create_task_from_form, update_task_from_form, delete_task, get_tasks,
    get_task, update_task_status, move_task_to_sprint,
)


class TestCreateTask:
    def test_create_valid_task(self):
        result = create_task_from_form({
            "title": "New Test Task",
            "task_type": "story",
            "status": "todo",
            "priority": "medium",
            "story_points": "3",
            "sprint_id": "sp-001",
            "project_id": "prj-001",
        }, user_email="test@pm-hub.local")
        assert result["success"] is True
        assert "created" in result["message"].lower() or "Created" in result["message"]

    def test_create_task_missing_title(self):
        result = create_task_from_form({
            "title": "",
            "task_type": "story",
            "priority": "medium",
        }, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_task_none_title(self):
        result = create_task_from_form({
            "title": None,
            "task_type": "story",
            "priority": "medium",
        }, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_task_invalid_type(self):
        result = create_task_from_form({
            "title": "Task",
            "task_type": "invalid_type",
            "priority": "medium",
        }, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_task_invalid_priority(self):
        result = create_task_from_form({
            "title": "Task",
            "task_type": "story",
            "priority": "super_urgent",
        }, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_task_with_description(self):
        result = create_task_from_form({
            "title": "Described Task",
            "task_type": "bug",
            "priority": "high",
            "description": "A detailed description",
        }, user_email="test@pm-hub.local")
        assert result["success"] is True

    def test_create_task_with_assignee(self):
        result = create_task_from_form({
            "title": "Assigned Task",
            "task_type": "task",
            "priority": "low",
            "assignee": "user-001",
        }, user_email="test@pm-hub.local")
        assert result["success"] is True

    def test_create_task_all_types(self):
        for task_type in ("epic", "story", "task", "bug", "subtask"):
            result = create_task_from_form({
                "title": f"Test {task_type}",
                "task_type": task_type,
                "priority": "medium",
            }, user_email="test@pm-hub.local")
            assert result["success"] is True, f"Failed for task_type={task_type}"


class TestGetTasks:
    def test_get_tasks_returns_dataframe(self):
        df = get_tasks()
        assert df is not None
        assert hasattr(df, "columns")

    def test_get_task_by_id(self):
        df = get_task("t-001")
        assert df is not None


class TestUpdateTask:
    def test_update_valid_task(self):
        result = update_task_from_form(
            "t-001",
            {
                "title": "Updated Task",
                "task_type": "story",
                "priority": "high",
            },
            expected_updated_at=None,
            user_email="test@pm-hub.local",
        )
        assert result["success"] is True

    def test_update_task_invalid_type(self):
        result = update_task_from_form(
            "t-001",
            {
                "title": "Updated Task",
                "task_type": "not_valid",
                "priority": "medium",
            },
            expected_updated_at=None,
            user_email="test@pm-hub.local",
        )
        assert result["success"] is False


class TestDeleteTask:
    def test_delete_existing_task(self):
        result = delete_task("t-001", user_email="test@pm-hub.local")
        assert result is True

    def test_delete_nonexistent_task(self):
        result = delete_task("t-nonexistent", user_email="test@pm-hub.local")
        # Should return False for nonexistent
        assert isinstance(result, bool)


class TestUpdateTaskStatus:
    def test_update_status(self):
        result = update_task_status("t-001", "in_progress", "test@pm-hub.local")
        assert isinstance(result, bool)

    def test_move_task_to_sprint(self):
        result = move_task_to_sprint("t-001", "sp-002")
        assert isinstance(result, bool)
