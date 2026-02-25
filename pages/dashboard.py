"""
Portfolio Dashboard — Home Page
================================
Top-level KPIs, portfolio health cards, project rollup.
"""

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from utils.data_access import get_portfolios, get_portfolio_projects
from utils.charts import portfolio_health_donut, budget_burn_chart, COLORS

dash.register_page(__name__, path="/", name="Portfolio Dashboard")


# ─── KPI Card Component ────────────────────────────────────
def kpi_card(label, value, sub_text, sub_color=None):
    return dbc.Card(
        dbc.CardBody([
            html.Div(label, className="kpi-label"),
            html.Div(str(value), className="kpi-value",
                     style={"color": sub_color} if sub_color else {}),
            html.Div(sub_text, className="kpi-sub",
                     style={"color": sub_color} if sub_color else {}),
        ]),
        className="kpi-card",
    )


# ─── Portfolio Card Component ──────────────────────────────
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
            # Stats row
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
            # Project list placeholder - populated by callback
            html.Div(id=f"projects-{portfolio['portfolio_id']}", className="project-list"),
        ]),
    ], className="portfolio-card")


# ─── Page Layout ────────────────────────────────────────────
def layout():
    portfolios = get_portfolios()

    # Calculate KPIs
    total_projects = portfolios["project_count"].sum() if not portfolios.empty else 0
    avg_completion = portfolios["avg_completion"].mean() if not portfolios.empty else 0
    total_budget = portfolios["total_budget"].sum() if not portfolios.empty else 0
    total_spent = portfolios["total_spent"].sum() if not portfolios.empty else 0

    green_count = len(portfolios[portfolios["health"] == "green"]) if not portfolios.empty else 0
    yellow_count = len(portfolios[portfolios["health"] == "yellow"]) if not portfolios.empty else 0
    red_count = len(portfolios[portfolios["health"] == "red"]) if not portfolios.empty else 0

    return html.Div([
        # KPI Strip
        dbc.Row([
            dbc.Col(kpi_card("Active Projects", int(total_projects),
                             f"across {len(portfolios)} portfolios"), width=2),
            dbc.Col(kpi_card("On Track", f"{green_count}/{len(portfolios)}",
                             "portfolios healthy", COLORS["green"]), width=2),
            dbc.Col(kpi_card("Avg Completion", f"{avg_completion:.0f}%",
                             "across all projects"), width=2),
            dbc.Col(kpi_card("Total Budget", f"${total_budget:,.0f}",
                             f"${total_spent:,.0f} spent"), width=3),
            dbc.Col(kpi_card("Budget Burned", f"{(total_spent/max(total_budget,1)*100):.0f}%",
                             "of total allocation",
                             COLORS["yellow"] if total_spent/max(total_budget,1) > 0.7 else COLORS["green"]),
                    width=3),
        ], className="kpi-strip mb-4"),

        # Portfolio health donut + portfolio cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Portfolio Health"),
                    dbc.CardBody(
                        dcc.Graph(
                            figure=portfolio_health_donut(
                                green_count, yellow_count, red_count
                            ),
                            config={"displayModeBar": False},
                            style={"height": "300px"},
                        )
                    ),
                ], className="chart-card"),
            ], width=4),
            dbc.Col([
                html.Div([
                    portfolio_card(row.to_dict())
                    for _, row in portfolios.iterrows()
                ] if not portfolios.empty else [
                    html.Div("No portfolios found.", className="text-muted p-4")
                ], className="portfolios-list"),
            ], width=8),
        ]),

        # Auto-refresh every 60 seconds
        dcc.Interval(id="refresh-interval", interval=60_000, n_intervals=0),
    ])
