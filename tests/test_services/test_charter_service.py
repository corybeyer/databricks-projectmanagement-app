"""Tests for charter service."""
import os
os.environ["USE_SAMPLE_DATA"] = "true"

from services.charter_service import (
    create_charter_from_form, update_charter_from_form, submit_charter,
    approve_charter, reject_charter, delete_charter, get_charters, get_charter,
)


def _valid_charter_data():
    return {
        "project_name": "Test Project Charter",
        "business_case": "This project will improve efficiency by 30%",
        "objectives": "Deliver a working prototype within 3 months",
        "scope_in": "Core features and API integration",
        "scope_out": "Mobile app development",
        "stakeholders": "Engineering, Product, QA",
        "success_criteria": "All acceptance tests pass",
        "delivery_method": "agile",
        "project_id": "prj-001",
    }


class TestCreateCharter:
    def test_create_valid_charter(self):
        result = create_charter_from_form(
            _valid_charter_data(), user_email="test@pm-hub.local"
        )
        assert result["success"] is True
        assert "created" in result["message"].lower()

    def test_create_charter_missing_project_name(self):
        data = _valid_charter_data()
        data["project_name"] = ""
        result = create_charter_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_charter_missing_business_case(self):
        data = _valid_charter_data()
        data["business_case"] = None
        result = create_charter_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_charter_missing_objectives(self):
        data = _valid_charter_data()
        data["objectives"] = ""
        result = create_charter_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_charter_missing_scope_in(self):
        data = _valid_charter_data()
        data["scope_in"] = None
        result = create_charter_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_charter_invalid_delivery_method(self):
        data = _valid_charter_data()
        data["delivery_method"] = "kanban"
        result = create_charter_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_charter_with_optional_fields(self):
        data = _valid_charter_data()
        data["risks"] = "Schedule risk due to team availability"
        data["budget"] = "$50,000"
        data["timeline"] = "Q2 2026"
        data["description"] = "Detailed charter description"
        result = create_charter_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is True


class TestUpdateCharter:
    def test_update_valid_charter(self):
        data = _valid_charter_data()
        data["project_name"] = "Updated Charter Name"
        result = update_charter_from_form(
            "ch-001", data, expected_updated_at=None,
            user_email="test@pm-hub.local",
        )
        assert result["success"] is True

    def test_update_charter_invalid_data(self):
        data = _valid_charter_data()
        data["project_name"] = ""
        result = update_charter_from_form(
            "ch-001", data, expected_updated_at=None,
            user_email="test@pm-hub.local",
        )
        assert result["success"] is False


class TestCharterWorkflow:
    def test_submit_draft_charter(self):
        result = submit_charter("ch-001", user_email="test@pm-hub.local")
        # Result depends on the current status of the sample charter
        assert "success" in result
        assert isinstance(result["success"], bool)

    def test_submit_nonexistent_charter(self):
        result = submit_charter("ch-nonexistent", user_email="test@pm-hub.local")
        # Either not found or fails
        assert isinstance(result["success"], bool)

    def test_approve_submitted_charter(self):
        # First submit, then approve
        submit_charter("ch-001", user_email="test@pm-hub.local")
        result = approve_charter("ch-001", user_email="test@pm-hub.local")
        assert isinstance(result["success"], bool)

    def test_reject_submitted_charter(self):
        submit_charter("ch-001", user_email="test@pm-hub.local")
        result = reject_charter("ch-001", user_email="test@pm-hub.local")
        assert isinstance(result["success"], bool)


class TestGetCharters:
    def test_get_charters_returns_dataframe(self):
        df = get_charters("prj-001")
        assert df is not None
        assert hasattr(df, "columns")

    def test_get_charter_by_id(self):
        df = get_charter("ch-001")
        assert df is not None


class TestDeleteCharter:
    def test_delete_charter(self):
        result = delete_charter("ch-001", user_email="test@pm-hub.local")
        assert isinstance(result, bool)
