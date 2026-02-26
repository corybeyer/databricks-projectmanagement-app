"""
Portfolios Page
================
Portfolio list with drill-down, budget burn chart, strategic bubble chart.
"""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from services.auth_service import get_user_token
from services.portfolio_service import get_dashboard_data, get_portfolio_projects
from components.kpi_card import kpi_card
from components.health_badge import health_badge
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from charts.theme import COLORS
from charts.portfolio_charts import budget_burn_chart, strategic_bubble_chart

dash.register_page(__name__, path="/portfolios", name="Portfolios")


def _project_row(project):
    """Render a single project row inside a portfolio."""
    pct = project.get("pct_complete", 0)
    return dbc.ListGroupItem([
        dbc.Row([
            dbc.Col([
                html.Div(project["name"], className="fw-bold"),
                html.Small(
                    f"{project.get('delivery_method', 'N/A')} · "
                    f"{project.get('current_phase_name', 'N/A')}",
                    className="text-muted",
                ),
            ], width=5),
            dbc.Col([
                dbc.Progress(
                    value=pct, label=f"{pct:.0f}%",
                    color="success" if pct >= 70 else "warning" if pct >= 40 else "info",
                    className="my-1",
                    style={"height": "18px"},
                ),
            ], width=4),
            dbc.Col([
                health_badge(project.get("health", "green")),
            ], width=3, className="text-end"),
        ], align="center"),
    ], className="bg-transparent border-secondary")


def layout():
    token = get_user_token()
    data = get_dashboard_data(user_token=token)
    portfolios = data["portfolios"]
    projects = get_portfolio_projects("pf-001", user_token=token)

    return html.Div([
        html.H4("Portfolios", className="page-title mb-3"),
        html.P(
            "Strategic portfolio overview with project health, budget burn, "
            "and value alignment.",
            className="page-subtitle mb-4",
        ),

        # KPI strip
        dbc.Row([
            dbc.Col(kpi_card("Portfolios", len(portfolios), "active portfolios"), width=3),
            dbc.Col(kpi_card("Total Projects", int(data["total_projects"]),
                             "across all portfolios"), width=3),
            dbc.Col(kpi_card("Total Budget", f"${data['total_budget']:,.0f}",
                             f"${data['total_spent']:,.0f} spent"), width=3),
            dbc.Col(kpi_card("Avg Completion", f"{data['avg_completion']:.0f}%",
                             "portfolio average"), width=3),
        ], className="kpi-strip mb-4"),

        # Charts row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Budget Burn by Project"),
                    dbc.CardBody(
                        dcc.Graph(
                            figure=budget_burn_chart(projects),
                            config={"displayModeBar": False},
                        ) if not projects.empty else empty_state("No project data.")
                    ),
                ], className="chart-card"),
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Strategic Alignment"),
                    dbc.CardBody(
                        dcc.Graph(
                            figure=strategic_bubble_chart(projects),
                            config={"displayModeBar": False},
                        ) if not projects.empty else empty_state("No project data.")
                    ),
                ], className="chart-card"),
            ], width=6),
        ], className="mb-4"),

        # Portfolio detail sections
        html.Div([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.Span(row["name"], className="fw-bold me-2"),
                        health_badge(row.get("health", "green")),
                    ], className="d-flex align-items-center"),
                ]),
                dbc.CardBody([
                    dbc.ListGroup([
                        _project_row(proj.to_dict())
                        for _, proj in get_portfolio_projects(
                            row["portfolio_id"], user_token=token
                        ).iterrows()
                    ]) if True else empty_state("No projects."),
                ]),
            ], className="mb-3")
            for _, row in portfolios.iterrows()
        ] if not portfolios.empty else [empty_state("No portfolios found.")]),

        auto_refresh(),
    ])
