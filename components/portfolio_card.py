"""Portfolio Card — portfolio summary with health badge and stats."""

from dash import html
import dash_bootstrap_components as dbc
from charts.theme import COLORS


def portfolio_card(portfolio):
    health_colors = {"green": COLORS["green"], "yellow": COLORS["yellow"], "red": COLORS["red"]}
    health_labels = {"green": "ON TRACK", "yellow": "AT RISK", "red": "OFF TRACK"}
    h = portfolio.get("health", "green")

    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.Div(portfolio["name"], className="portfolio-name"),
                html.Div(
                    f"{portfolio.get('project_count', 0)} projects · "
                    f"${portfolio.get('total_budget', 0):,.0f} budget",
                    className="portfolio-meta",
                ),
            ]),
            html.Div([
                html.Span("● ", style={"color": health_colors[h]}),
                html.Span(health_labels[h], style={"color": health_colors[h]}),
            ], className="portfolio-health-badge"),
        ], className="portfolio-card-header"),
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.Div("Completion", className="stat-label"),
                    html.Div(f"{portfolio.get('avg_completion', 0):.0f}%", className="stat-value"),
                ], className="stat-item"),
                html.Div([
                    html.Div("Budget Used", className="stat-label"),
                    html.Div(
                        f"{(portfolio.get('total_spent', 0) / max(portfolio.get('total_budget', 1), 1) * 100):.0f}%",
                        className="stat-value",
                    ),
                ], className="stat-item"),
            ], className="stats-row"),
            html.Div(id=f"projects-{portfolio['portfolio_id']}", className="project-list"),
        ]),
    ], className="portfolio-card")
