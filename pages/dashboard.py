"""
Portfolio Dashboard — Home Page
================================
Top-level KPIs, portfolio health cards, project rollup.
"""

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
from services.auth_service import get_user_token
from services.portfolio_service import get_dashboard_data
from components.kpi_card import kpi_card
from components.portfolio_card import portfolio_card
from components.auto_refresh import auto_refresh
from charts.theme import COLORS
from charts.portfolio_charts import portfolio_health_donut

dash.register_page(__name__, path="/", name="Portfolio Dashboard")


def _build_content():
    """Build the actual page content."""
    token = get_user_token()
    data = get_dashboard_data(user_token=token)
    portfolios = data["portfolios"]

    return html.Div([
        # KPI Strip
        dbc.Row([
            dbc.Col(kpi_card("Active Projects", int(data["total_projects"]),
                             f"across {len(portfolios)} portfolios"), width=2),
            dbc.Col(kpi_card("On Track", f"{data['green_count']}/{len(portfolios)}",
                             "portfolios healthy", COLORS["green"]), width=2),
            dbc.Col(kpi_card("Avg Completion", f"{data['avg_completion']:.0f}%",
                             "across all projects"), width=2),
            dbc.Col(kpi_card("Total Budget", f"${data['total_budget']:,.0f}",
                             f"${data['total_spent']:,.0f} spent"), width=3),
            dbc.Col(kpi_card("Budget Burned",
                             f"{(data['total_spent']/max(data['total_budget'],1)*100):.0f}%",
                             "of total allocation",
                             COLORS["yellow"] if data["total_spent"]/max(data["total_budget"],1) > 0.7 else COLORS["green"]),
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
                                data["green_count"], data["yellow_count"], data["red_count"]
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
    ])


def layout():
    return html.Div([
        html.Div(id="dashboard-content"),
        auto_refresh(interval_id="dashboard-refresh-interval"),
    ])


@callback(
    Output("dashboard-content", "children"),
    Input("dashboard-refresh-interval", "n_intervals"),
)
def refresh_dashboard(n):
    return _build_content()
