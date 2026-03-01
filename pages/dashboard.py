"""
Portfolio Dashboard — Home Page
================================
Top-level KPIs, department overview, portfolio health cards, project rollup.
"""

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
from services.auth_service import get_user_token
from services.portfolio_service import get_dashboard_data
from services.department_service import get_department_hierarchy
from components.kpi_card import kpi_card
from components.portfolio_card import portfolio_card
from components.auto_refresh import auto_refresh
from charts.theme import COLORS
from charts.portfolio_charts import portfolio_health_donut
from utils.url_state import set_params

dash.register_page(__name__, path="/", name="Portfolio Dashboard")


def _dept_card(dept):
    """Render a department overview card with drill-down link."""
    return dbc.Col([
        dcc.Link(
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="bi bi-building me-2"),
                        html.Span(dept.get("name", "Department"), className="fw-bold"),
                    ], className="mb-2"),
                    dbc.Row([
                        dbc.Col([
                            html.Div(str(int(dept.get("portfolio_count", 0))),
                                     className="fs-5 fw-bold"),
                            html.Small("Portfolios", className="text-muted"),
                        ], className="text-center"),
                        dbc.Col([
                            html.Div(str(int(dept.get("member_count", 0))),
                                     className="fs-5 fw-bold"),
                            html.Small("Members", className="text-muted"),
                        ], className="text-center"),
                    ]),
                ]),
            ], className="h-100"),
            href=set_params("/portfolios", department_id=dept.get("department_id")),
            style={"textDecoration": "none", "color": "inherit"},
        ),
    ], width=3, className="mb-3")


def _build_content(department_id=None):
    """Build the actual page content."""
    token = get_user_token()
    data = get_dashboard_data(department_id=department_id, user_token=token)
    portfolios = data["portfolios"]

    # Department overview row
    dept_section = html.Div()
    if not department_id:
        depts = get_department_hierarchy(user_token=token)
        if not depts.empty:
            dept_section = html.Div([
                html.H6("Departments", className="text-muted mb-2"),
                dbc.Row([
                    _dept_card(row.to_dict())
                    for _, row in depts.iterrows()
                ]),
            ], className="mb-4")

    return html.Div([
        # Page header
        html.Div([
            html.Div(html.I(className="bi bi-grid-1x2-fill"), className="page-header-icon"),
            html.H4("Portfolio Dashboard", className="page-title"),
        ], className="page-header mb-3"),

        # KPI Strip
        dbc.Row([
            dbc.Col(kpi_card("Active Projects", int(data["total_projects"]),
                             f"across {len(portfolios)} portfolios",
                             icon="folder-fill", icon_color="blue"), md=True),
            dbc.Col(kpi_card("On Track", f"{data['green_count']}/{len(portfolios)}",
                             "portfolios healthy", COLORS["green"],
                             icon="check-circle-fill", icon_color="green"), md=True),
            dbc.Col(kpi_card("Avg Completion", f"{data['avg_completion']:.0f}%",
                             "across all projects",
                             icon="pie-chart-fill", icon_color="purple"), md=True),
            dbc.Col(kpi_card("Total Budget", f"${data['total_budget']:,.0f}",
                             f"${data['total_spent']:,.0f} spent",
                             icon="currency-dollar", icon_color="cyan"), md=True),
            dbc.Col(kpi_card("Budget Burned",
                             f"{(data['total_spent']/max(data['total_budget'],1)*100):.0f}%",
                             "of total allocation",
                             COLORS["yellow"] if data["total_spent"]/max(data["total_budget"],1) > 0.7 else COLORS["green"],
                             icon="fire", icon_color="yellow"),
                    md=True),
        ], className="kpi-strip mb-4"),

        # Department cards
        dept_section,

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
                            style={"height": "380px"},
                        )
                    ),
                ], className="chart-card h-100"),
            ], md=5),
            dbc.Col([
                html.Div([
                    portfolio_card(row.to_dict())
                    for _, row in portfolios.iterrows()
                ] if not portfolios.empty else [
                    html.Div("No portfolios found.", className="text-muted p-4")
                ], className="portfolios-list"),
            ], md=7),
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
    Input("active-department-store", "data"),
)
def refresh_dashboard(n, department_id):
    return _build_content(department_id=department_id)
