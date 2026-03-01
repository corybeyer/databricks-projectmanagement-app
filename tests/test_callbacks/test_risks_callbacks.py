"""Callback tests for risks page."""

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

from pages.risks import (
    refresh_risks, toggle_heatmap, save_risk, confirm_delete_risk,
    cancel_risk_modal, RISK_FIELDS,
)


class TestRefreshRisks:
    def test_returns_content(self):
        result = refresh_risks(1, 0, False, None, None, None, None)
        assert result is not None
        assert isinstance(result, html.Div)

    def test_with_residual_heatmap(self):
        result = refresh_risks(1, 0, True, None, None, None, None)
        assert result is not None

    def test_with_status_filter(self):
        result = refresh_risks(1, 0, False, ["identified"], None, None, None)
        assert result is not None

    def test_with_category_filter(self):
        result = refresh_risks(1, 0, False, None, ["technical"], None, None)
        assert result is not None

    def test_with_owner_search(self):
        result = refresh_risks(1, 0, False, None, None, "Cory", None)
        assert result is not None

    def test_with_sort(self):
        result = refresh_risks(1, 0, False, None, None, None, "risk_score")
        assert result is not None


class TestToggleHeatmap:
    def test_toggle_from_false(self):
        result = toggle_heatmap(1, False)
        assert result is True

    def test_toggle_from_true(self):
        result = toggle_heatmap(1, True)
        assert result is False

    def test_toggle_from_none(self):
        result = toggle_heatmap(1, None)
        assert result is True


class TestSaveRisk:
    def _num_outputs(self):
        return 6 + len(RISK_FIELDS) * 2

    def test_no_click_returns_no_update(self):
        result = save_risk(0, None, 0, *[None] * len(RISK_FIELDS))
        assert all(v is no_update for v in result)
        assert len(result) == self._num_outputs()

    def test_create_valid_risk(self):
        # field order: title, category, probability, impact, response_strategy,
        #              owner, response_owner, mitigation_plan, contingency_plan,
        #              trigger_conditions, risk_proximity, risk_urgency
        fields = [
            "Test Risk", "technical", 3, 4, "mitigate",
            "Risk Owner", "Response Owner", "Mitigate it", "Plan B",
            "If X happens", "near_term", 3,
        ]
        result = save_risk(1, None, 0, *fields)
        assert result[0] is False  # modal closes
        assert result[1] == 1  # counter incremented
        assert result[4] == "success"

    def test_create_missing_title(self):
        fields = [
            "", "technical", 3, 4, None,
            "", "", "", "",
            "", None, None,
        ]
        result = save_risk(1, None, 0, *fields)
        assert result[0] is True  # modal stays open
        assert result[1] is no_update
        assert result[4] == "danger"

    def test_update_existing_risk(self):
        import json
        from services import risk_service
        # Read current updated_at to satisfy optimistic locking
        risk_df = risk_service.get_risk("r-001")
        updated_at = str(risk_df.iloc[0].get("updated_at", "")) if not risk_df.empty else ""
        stored = json.dumps({"risk_id": "r-001", "updated_at": updated_at})
        fields = [
            "Updated Risk", "schedule", 4, 5, "avoid",
            "New Owner", "", "Updated plan", "",
            "", "mid_term", 4,
        ]
        result = save_risk(1, stored, 2, *fields)
        assert result[0] is False  # modal closes
        assert result[1] == 3  # counter 2+1


class TestConfirmDeleteRisk:
    def test_no_click_returns_no_update(self):
        result = confirm_delete_risk(0, "risk-001", 0)
        assert all(v is no_update for v in result)

    def test_no_risk_id(self):
        result = confirm_delete_risk(1, None, 0)
        assert all(v is no_update for v in result)

    def test_delete_success(self):
        # Use existing sample data risk ID
        result = confirm_delete_risk(1, "r-001", 4)
        assert result[0] is False  # modal closes
        assert result[1] == 5  # counter 4+1
        assert result[4] == "success"


class TestCancelRiskModal:
    def test_returns_false(self):
        result = cancel_risk_modal(1)
        assert result is False
