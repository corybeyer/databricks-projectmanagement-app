"""
Roadmap Timeline Page
======================
Cross-portfolio project timeline with health-coded bars and today marker.
"""

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
from services.auth_service import get_user_token
from services.portfolio_service import get_portfolio_projects
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from charts.portfolio_charts import roadmap_chart

dash.register_page(__name__, path="/roadmap", name="Roadmap Timeline")


def _build_content():
    """Build the actual page content."""
    token = get_user_token()
    projects = get_portfolio_projects("pf-001", user_token=token)

    return html.Div([
        html.H4("Roadmap Timeline", className="page-title mb-3"),
        html.P(
            "Cross-portfolio project timeline showing start dates, target dates, "
            "and current health status.",
            className="page-subtitle mb-4",
        ),

        dbc.Card([
            dbc.CardHeader("Project Timeline"),
            dbc.CardBody(
                dcc.Graph(
                    figure=roadmap_chart(projects),
                    config={"displayModeBar": False},
                    style={"height": "500px"},
                ) if not projects.empty else empty_state("No project data available.")
            ),
        ], className="chart-card"),
    ])


def layout():
    return html.Div([
        html.Div(id="roadmap-content"),
        auto_refresh(interval_id="roadmap-refresh-interval"),
    ])


@callback(
    Output("roadmap-content", "children"),
    Input("roadmap-refresh-interval", "n_intervals"),
)
def refresh_roadmap(n):
    return _build_content()
