"""Tests for portfolio service."""
import os
os.environ["USE_SAMPLE_DATA"] = "true"

from services.portfolio_service import (
    create_portfolio_from_form, update_portfolio_from_form, delete_portfolio,
    get_dashboard_data, get_portfolio_projects, get_portfolio,
)


def _valid_portfolio_data():
    return {
        "name": "New Test Portfolio",
        "owner": "Test User",
    }


class TestCreatePortfolio:
    def test_create_valid_portfolio(self):
        result = create_portfolio_from_form(
            _valid_portfolio_data(), user_email="test@pm-hub.local"
        )
        assert result["success"] is True
        assert "created" in result["message"].lower()

    def test_create_portfolio_missing_name(self):
        data = _valid_portfolio_data()
        data["name"] = ""
        result = create_portfolio_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_portfolio_missing_owner(self):
        data = _valid_portfolio_data()
        data["owner"] = ""
        result = create_portfolio_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is False

    def test_create_portfolio_with_optional_fields(self):
        data = _valid_portfolio_data()
        data["description"] = "A test portfolio"
        data["strategic_priority"] = "Digital Transformation"
        data["department_id"] = "dept-001"
        result = create_portfolio_from_form(data, user_email="test@pm-hub.local")
        assert result["success"] is True


class TestUpdatePortfolio:
    def test_update_valid_portfolio(self):
        data = _valid_portfolio_data()
        data["name"] = "Updated Portfolio Name"
        result = update_portfolio_from_form(
            "pf-001", data, expected_updated_at=None,
            user_email="test@pm-hub.local",
        )
        assert result["success"] is True

    def test_update_portfolio_invalid_data(self):
        data = _valid_portfolio_data()
        data["name"] = ""
        result = update_portfolio_from_form(
            "pf-001", data, expected_updated_at=None,
            user_email="test@pm-hub.local",
        )
        assert result["success"] is False


class TestDeletePortfolio:
    def test_delete_portfolio(self):
        result = delete_portfolio("pf-001", user_email="test@pm-hub.local")
        assert isinstance(result, bool)


class TestDashboardData:
    def test_get_dashboard_data(self):
        data = get_dashboard_data()
        assert isinstance(data, dict)
        assert "portfolios" in data
        assert "total_projects" in data
        assert "avg_completion" in data
        assert "total_budget" in data
        assert "total_spent" in data
        assert "green_count" in data
        assert "yellow_count" in data
        assert "red_count" in data

    def test_dashboard_data_types(self):
        data = get_dashboard_data()
        assert isinstance(data["total_projects"], int)
        assert isinstance(data["avg_completion"], (int, float))
        assert isinstance(data["total_budget"], (int, float))


class TestGetPortfolio:
    def test_get_portfolio_by_id(self):
        df = get_portfolio("pf-001")
        assert df is not None

    def test_get_portfolio_projects(self):
        df = get_portfolio_projects("pf-001")
        assert df is not None
        assert hasattr(df, "columns")
