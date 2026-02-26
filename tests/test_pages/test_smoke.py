"""Smoke tests — verify every page layout() returns valid components."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Set sample data mode
os.environ["USE_SAMPLE_DATA"] = "true"

import dash
from dash import Dash, html
import dash_bootstrap_components as dbc

# Create test app
app = Dash(__name__, use_pages=False, suppress_callback_exceptions=True,
           external_stylesheets=[dbc.themes.SLATE])


def test_dashboard_layout():
    from pages.dashboard import layout
    result = layout()
    assert result is not None
    assert isinstance(result, html.Div)


def test_charters_layout():
    from pages.charters import layout
    result = layout()
    assert result is not None
    assert isinstance(result, html.Div)
