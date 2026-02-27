"""
Resource Allocation Page
=========================
Team workload overview with utilization chart and member details.
"""

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
from services.auth_service import get_user_token
from services.analytics_service import get_resource_allocations
from components.kpi_card import kpi_card
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from components.filter_bar import filter_bar
from charts.theme import COLORS
from charts.analytics_charts import resource_utilization_chart

dash.register_page(__name__, path="/resources", name="Resource Allocation")

RESOURCES_FILTERS = [
    {"id": "role", "label": "Role", "type": "select", "multi": True,
     "options": [{"label": "Lead", "value": "lead"},
                 {"label": "Senior", "value": "senior"},
                 {"label": "Member", "value": "member"},
                 {"label": "Junior", "value": "junior"}]},
]


def _build_content(role_filter=None):
    """Build the actual page content."""
    token = get_user_token()
    resources = get_resource_allocations(user_token=token)

    # Apply filters
    if not resources.empty and role_filter and "role" in resources.columns:
        resources = resources[resources["role"].isin(role_filter)]

    if not resources.empty:
        team_count = resources["display_name"].nunique()
        total_tasks = int(resources["task_count"].sum())
        total_points = int(resources["points_assigned"].sum())
        done_points = int(resources["points_done"].sum())
    else:
        team_count = total_tasks = total_points = done_points = 0

    return html.Div([
        html.H4("Resource Allocation", className="page-title mb-3"),
        html.P(
            "Team workload distribution, task assignments, and capacity utilization "
            "across projects.",
            className="page-subtitle mb-4",
        ),

        # KPI strip
        dbc.Row([
            dbc.Col(kpi_card("Team Size", team_count, "active members"), width=3),
            dbc.Col(kpi_card("Active Tasks", total_tasks, "assigned"), width=3),
            dbc.Col(kpi_card("Points Assigned", total_points,
                             f"{done_points} completed"), width=3),
            dbc.Col(kpi_card("Completion Rate",
                             f"{(done_points/max(total_points,1)*100):.0f}%",
                             "points done vs assigned",
                             COLORS["green"]), width=3),
        ], className="kpi-strip mb-4"),

        # Utilization chart
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Team Utilization"),
                    dbc.CardBody(
                        dcc.Graph(
                            figure=resource_utilization_chart(resources),
                            config={"displayModeBar": False},
                        ) if not resources.empty else empty_state("No resource data.")
                    ),
                ], className="chart-card"),
            ], width=12),
        ], className="mb-4"),

        # Team member detail table
        dbc.Card([
            dbc.CardHeader("Team Member Details"),
            dbc.CardBody([
                dbc.Table([
                    html.Thead(html.Tr([
                        html.Th("Name"),
                        html.Th("Role"),
                        html.Th("Project"),
                        html.Th("Tasks", className="text-center"),
                        html.Th("Points", className="text-center"),
                        html.Th("Done", className="text-center"),
                        html.Th("Progress"),
                    ])),
                    html.Tbody([
                        html.Tr([
                            html.Td(row["display_name"], className="fw-bold"),
                            html.Td(dbc.Badge(
                                row.get("role", "member").title(),
                                color="primary" if row.get("role") == "lead" else "secondary",
                            )),
                            html.Td(html.Small(row.get("project_name", "N/A"))),
                            html.Td(str(row.get("task_count", 0)), className="text-center"),
                            html.Td(str(row.get("points_assigned", 0)), className="text-center"),
                            html.Td(str(row.get("points_done", 0)), className="text-center"),
                            html.Td(
                                dbc.Progress(
                                    value=(row.get("points_done", 0) / max(row.get("points_assigned", 1), 1) * 100),
                                    style={"height": "8px"},
                                    color="success",
                                ),
                            ),
                        ])
                        for _, row in resources.iterrows()
                    ]),
                ], bordered=False, hover=True, responsive=True,
                    className="table-dark table-sm"),
            ] if not resources.empty else [empty_state("No team data available.")]),
        ]),
    ])


def layout():
    return html.Div([
        # Filters
        filter_bar("resources", RESOURCES_FILTERS),

        html.Div(id="resources-content"),
        auto_refresh(interval_id="resources-refresh-interval"),
    ])


@callback(
    Output("resources-content", "children"),
    Input("resources-refresh-interval", "n_intervals"),
    Input("resources-role-filter", "value"),
)
def refresh_resources(n, role_filter):
    return _build_content(role_filter=role_filter)
