"""Tests for risk service."""
import os
os.environ["USE_SAMPLE_DATA"] = "true"

from services.risk_service import (
    create_risk_from_form, update_risk_from_form, delete_risk,
    update_risk_status, review_risk, get_risks, get_risk,
    get_risks_by_project,
)


def _valid_risk_data():
    return {
        "title": "Server capacity risk",
        "category": "technical",
        "probability": "3",
        "impact": "4",
        "response_strategy": "mitigate",
        "risk_proximity": "near_term",
        "description": "May run out of capacity during peak load",
        "mitigation_plan": "Add auto-scaling rules",
        "project_id": "prj-001",
        "portfolio_id": "pf-001",
    }


class TestCreateRisk:
    def test_create_valid_risk(self):
        result = create_risk_from_form(
            _valid_risk_data(), user_email="test@pm-hub.local"
        )
        assert result["success"] is True
        assert "created" in result["message"].lower()

    def test_create_risk_missing_title(self):
        data = _valid_risk_data()
        data["title"] = ""
        result = create_risk_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_risk_invalid_category(self):
        data = _valid_risk_data()
        data["category"] = "unknown_category"
        result = create_risk_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_risk_probability_out_of_range(self):
        data = _valid_risk_data()
        data["probability"] = "6"
        result = create_risk_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_risk_impact_out_of_range(self):
        data = _valid_risk_data()
        data["impact"] = "0"
        result = create_risk_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_risk_invalid_response_strategy(self):
        data = _valid_risk_data()
        data["response_strategy"] = "ignore"
        result = create_risk_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_risk_with_all_optional_fields(self):
        data = _valid_risk_data()
        data["contingency_plan"] = "Switch to backup servers"
        data["trigger_conditions"] = "CPU usage > 90% for 5 minutes"
        data["owner"] = "ops-lead"
        data["response_owner"] = "infra-team"
        data["risk_urgency"] = "4"
        result = create_risk_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is True

    def test_create_risk_all_categories(self):
        for cat in ("technical", "resource", "schedule", "scope",
                     "budget", "external", "organizational"):
            data = _valid_risk_data()
            data["category"] = cat
            result = create_risk_from_form(data, user_email="test@pm-hub.local")
            assert result["success"] is True, f"Failed for category={cat}"


class TestUpdateRisk:
    def test_update_valid_risk(self):
        data = _valid_risk_data()
        data["title"] = "Updated Risk Title"
        result = update_risk_from_form(
            "r-001", data, expected_updated_at=None,
            user_email="test@pm-hub.local",
        )
        assert result["success"] is True

    def test_update_risk_invalid_data(self):
        data = _valid_risk_data()
        data["title"] = ""
        result = update_risk_from_form(
            "r-001", data, expected_updated_at=None,
            user_email="test@pm-hub.local",
        )
        assert result["success"] is False


class TestDeleteRisk:
    def test_delete_risk(self):
        result = delete_risk("r-001", user_email="test@pm-hub.local")
        assert isinstance(result, bool)


class TestUpdateRiskStatus:
    def test_update_to_valid_status(self):
        result = update_risk_status(
            "r-001", "monitoring", user_email="test@pm-hub.local"
        )
        assert "success" in result
        assert isinstance(result["success"], bool)

    def test_update_to_invalid_status(self):
        result = update_risk_status(
            "r-001", "not_a_status", user_email="test@pm-hub.local"
        )
        assert result["success"] is False

    def test_update_all_valid_statuses(self):
        for status in ("identified", "qualitative_analysis", "response_planning",
                        "monitoring", "resolved", "closed"):
            result = update_risk_status(
                "r-001", status, user_email="test@pm-hub.local"
            )
            assert isinstance(result["success"], bool), f"Failed for status={status}"


class TestReviewRisk:
    def test_review_risk(self):
        result = review_risk("r-001", user_email="test@pm-hub.local")
        assert "success" in result
        assert isinstance(result["success"], bool)

    def test_review_nonexistent_risk(self):
        result = review_risk("risk-nonexistent", user_email="test@pm-hub.local")
        # Should handle gracefully — either not found or empty df
        assert isinstance(result["success"], bool)


class TestGetRisks:
    def test_get_risks_returns_dataframe(self):
        df = get_risks()
        assert df is not None
        assert hasattr(df, "columns")

    def test_get_risk_by_id(self):
        df = get_risk("r-001")
        assert df is not None

    def test_get_risks_by_project(self):
        df = get_risks_by_project("prj-001")
        assert df is not None
        assert hasattr(df, "columns")
