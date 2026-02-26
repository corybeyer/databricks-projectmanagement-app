"""
Risk Register Page
===================
Risk heatmap and risk table with severity, owner, and status.
"""

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
from services.auth_service import get_user_token
from services.analytics_service import get_risks
from components.kpi_card import kpi_card
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from charts.theme import COLORS
from charts.analytics_charts import risk_heatmap

dash.register_page(__name__, path="/risks", name="Risk Register")


def _risk_status_badge(status):
    """Render a risk status badge."""
    color_map = {
        "open": "danger", "mitigating": "warning",
        "accepted": "info", "closed": "secondary",
    }
    return dbc.Badge(
        status.replace("_", " ").title(),
        color=color_map.get(status, "secondary"),
        className="me-1",
    )


def _risk_score_display(score):
    """Render a colored risk score."""
    if score >= 15:
        color = COLORS["red"]
    elif score >= 8:
        color = COLORS["yellow"]
    else:
        color = COLORS["green"]
    return html.Span(str(score), style={"color": color, "fontWeight": "bold"})


def _build_content():
    """Build the actual page content."""
    token = get_user_token()
    risks = get_risks(user_token=token)

    if not risks.empty:
        total = len(risks)
        high_risks = len(risks[risks["risk_score"] >= 15])
        avg_score = risks["risk_score"].mean()
        open_risks = len(risks[risks["status"].isin(["open", "mitigating"])])
    else:
        total = high_risks = open_risks = 0
        avg_score = 0.0

    return html.Div([
        html.H4("Risk Register", className="page-title mb-3"),
        html.P(
            "Track and manage project and portfolio risks with probability/impact "
            "assessment and mitigation status.",
            className="page-subtitle mb-4",
        ),

        # KPI strip
        dbc.Row([
            dbc.Col(kpi_card("Total Risks", total, "registered"), width=3),
            dbc.Col(kpi_card("High Severity", high_risks, "score >= 15",
                             COLORS["red"] if high_risks > 0 else None), width=3),
            dbc.Col(kpi_card("Avg Score", f"{avg_score:.1f}", "across all risks"), width=3),
            dbc.Col(kpi_card("Open / Active", open_risks, "need attention",
                             COLORS["yellow"] if open_risks > 0 else None), width=3),
        ], className="kpi-strip mb-4"),

        # Heatmap + table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Risk Heatmap"),
                    dbc.CardBody(
                        dcc.Graph(
                            figure=risk_heatmap(risks),
                            config={"displayModeBar": False},
                        ) if not risks.empty else empty_state("No risk data.")
                    ),
                ], className="chart-card"),
            ], width=5),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Risk Details"),
                    dbc.CardBody([
                        dbc.Table([
                            html.Thead(html.Tr([
                                html.Th("Risk", style={"width": "35%"}),
                                html.Th("Project"),
                                html.Th("Score", className="text-center"),
                                html.Th("Status"),
                                html.Th("Owner"),
                            ])),
                            html.Tbody([
                                html.Tr([
                                    html.Td([
                                        html.Div(row["title"], className="fw-bold small"),
                                        html.Small(
                                            row.get("category", "").title(),
                                            className="text-muted",
                                        ),
                                    ]),
                                    html.Td(
                                        html.Small(row.get("project_name", "N/A")),
                                    ),
                                    html.Td(
                                        _risk_score_display(row["risk_score"]),
                                        className="text-center",
                                    ),
                                    html.Td(_risk_status_badge(row["status"])),
                                    html.Td(
                                        html.Small(row.get("owner", "Unassigned")),
                                    ),
                                ])
                                for _, row in risks.iterrows()
                            ]),
                        ], bordered=False, hover=True, responsive=True,
                            className="table-dark table-sm"),
                    ] if not risks.empty else [empty_state("No risks found.")]),
                ], className="chart-card"),
            ], width=7),
        ]),
    ])


def layout():
    return html.Div([
        html.Div(id="risks-content"),
        auto_refresh(interval_id="risks-refresh-interval"),
    ])


@callback(
    Output("risks-content", "children"),
    Input("risks-refresh-interval", "n_intervals"),
)
def refresh_risks(n):
    return _build_content()
