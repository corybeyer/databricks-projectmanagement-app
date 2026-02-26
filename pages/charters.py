"""
Project Charters Page
======================
View and create formal project charter documents.
"""

import dash
from dash import html, callback, Input, Output
import dash_bootstrap_components as dbc
from services.auth_service import get_user_token
from services.project_service import get_project_charter
from components.charter_display import charter_display
from components.charter_form import charter_form
from components.auto_refresh import auto_refresh

dash.register_page(__name__, path="/charters", name="Project Charters")


def _build_content():
    """Build the actual page content."""
    token = get_user_token()
    charter_data = get_project_charter("prj-001", user_token=token)

    return html.Div([
        html.H4("Project Charters", className="page-title mb-3"),
        html.P(
            "Formal project authorization documents. Each charter defines the business case, "
            "scope, objectives, delivery method, and governance structure.",
            className="page-subtitle mb-4",
        ),

        dbc.Tabs([
            dbc.Tab(
                charter_display(charter_data),
                label="Unity Catalog Migration",
                tab_id="charter-uc",
            ),
            dbc.Tab(
                html.Div("Select a project to view its charter.", className="p-4 text-muted"),
                label="DLT Pipeline Framework",
                tab_id="charter-dlt",
            ),
            dbc.Tab(
                charter_form(),
                label="+ New Charter",
                tab_id="charter-new",
            ),
        ], id="charter-tabs", active_tab="charter-uc"),
    ])


def layout():
    return html.Div([
        html.Div(id="charters-content"),
        auto_refresh(interval_id="charters-refresh-interval"),
    ])


@callback(
    Output("charters-content", "children"),
    Input("charters-refresh-interval", "n_intervals"),
)
def refresh_charters(n):
    return _build_content()
