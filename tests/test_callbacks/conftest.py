"""Shared fixtures for callback tests."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Force sample data mode
os.environ["USE_SAMPLE_DATA"] = "true"

import dash
from dash import Dash
import dash_bootstrap_components as dbc

# Create a minimal Dash app so register_page works during imports
_app = Dash(
    __name__,
    use_pages=False,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.SLATE],
)
