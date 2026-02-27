"""Tests for project service."""
import os
os.environ["USE_SAMPLE_DATA"] = "true"

from services.project_service import (
    create_project_from_form, update_project_from_form, delete_project,
    get_projects, get_project, get_project_detail, get_project_charter,
)


def _valid_project_data():
    return {
        "name": "New Test Project",
        "delivery_method": "agile",
        "status": "planning",
        "health": "green",
        "start_date": "2026-03-01",
        "owner": "Cory S.",
        "portfolio_id": "pf-001",
        "department_id": "dept-001",
    }


class TestCreateProject:
    def test_create_valid_project(self):
        result = create_project_from_form(
            _valid_project_data(), user_email="test@pm-hub.local"
        )
        assert result["success"] is True
        assert "created" in result["message"].lower()

    def test_create_project_missing_name(self):
        data = _valid_project_data()
        data["name"] = ""
        result = create_project_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_project_invalid_delivery_method(self):
        data = _valid_project_data()
        data["delivery_method"] = "scrum"
        result = create_project_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_project_invalid_status(self):
        data = _valid_project_data()
        data["status"] = "pending"
        result = create_project_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_project_invalid_health(self):
        data = _valid_project_data()
        data["health"] = "blue"
        result = create_project_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_project_missing_start_date(self):
        data = _valid_project_data()
        data["start_date"] = None
        result = create_project_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_project_missing_owner(self):
        data = _valid_project_data()
        data["owner"] = ""
        result = create_project_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_project_with_optional_fields(self):
        data = _valid_project_data()
        data["description"] = "Project description"
        data["target_date"] = "2026-09-01"
        data["budget_total"] = "500000"
        result = create_project_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is True

    def test_create_project_target_before_start(self):
        data = _valid_project_data()
        data["start_date"] = "2026-06-01"
        data["target_date"] = "2026-03-01"
        result = create_project_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_project_all_delivery_methods(self):
        for method in ("waterfall", "agile", "hybrid"):
            data = _valid_project_data()
            data["delivery_method"] = method
            result = create_project_from_form(data, user_email="test@pm-hub.local")
            assert result["success"] is True, f"Failed for delivery_method={method}"

    def test_create_project_all_statuses(self):
        for status in ("planning", "active", "on_hold", "completed", "cancelled"):
            data = _valid_project_data()
            data["status"] = status
            result = create_project_from_form(data, user_email="test@pm-hub.local")
            assert result["success"] is True, f"Failed for status={status}"


class TestUpdateProject:
    def test_update_valid_project(self):
        data = _valid_project_data()
        data["name"] = "Updated Project Name"
        result = update_project_from_form(
            "prj-001", data, expected_updated_at=None,
            user_email="test@pm-hub.local",
        )
        assert result["success"] is True

    def test_update_project_invalid_data(self):
        data = _valid_project_data()
        data["name"] = ""
        result = update_project_from_form(
            "prj-001", data, expected_updated_at=None,
            user_email="test@pm-hub.local",
        )
        assert result["success"] is False


class TestDeleteProject:
    def test_delete_project(self):
        result = delete_project("prj-001", user_email="test@pm-hub.local")
        assert isinstance(result, bool)


class TestGetProjects:
    def test_get_projects_returns_dataframe(self):
        df = get_projects()
        assert df is not None
        assert hasattr(df, "columns")

    def test_get_projects_by_portfolio(self):
        df = get_projects(portfolio_id="pf-001")
        assert df is not None

    def test_get_project_by_id(self):
        df = get_project("prj-001")
        assert df is not None

    def test_get_project_detail(self):
        df = get_project_detail("prj-001")
        assert df is not None

    def test_get_project_charter(self):
        df = get_project_charter("prj-001")
        assert df is not None
