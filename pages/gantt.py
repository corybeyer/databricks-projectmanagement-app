"""
Gantt Timeline Page
====================
Project phase Gantt chart with delivery method color coding.
"""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from services.auth_service import get_user_token
from services.project_service import get_project_phases, get_project_detail
from components.kpi_card import kpi_card
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from charts.theme import COLORS
from charts.project_charts import gantt_chart

dash.register_page(__name__, path="/gantt", name="Gantt Timeline")


def layout():
    token = get_user_token()
    phases = get_project_phases("prj-001", user_token=token)
    project = get_project_detail("prj-001", user_token=token)

    project_name = project.iloc[0]["name"] if not project.empty else "Project"

    if not phases.empty:
        total_phases = len(phases)
        done_phases = len(phases[phases["status"] == "done"])
        in_progress = len(phases[phases["status"] == "in_progress"])
    else:
        total_phases = done_phases = in_progress = 0

    return html.Div([
        html.H4("Gantt Timeline", className="page-title mb-1"),
        html.P(project_name, className="page-subtitle mb-3",
               style={"color": COLORS["accent"]}),

        # Phase KPIs
        dbc.Row([
            dbc.Col(kpi_card("Total Phases", total_phases, "in project"), width=3),
            dbc.Col(kpi_card("Completed", done_phases,
                             f"{(done_phases/max(total_phases,1)*100):.0f}% done",
                             COLORS["green"]), width=3),
            dbc.Col(kpi_card("In Progress", in_progress, "active now",
                             COLORS["accent"]), width=3),
            dbc.Col(kpi_card("Remaining", total_phases - done_phases - in_progress,
                             "not started"), width=3),
        ], className="kpi-strip mb-4"),

        # Gantt chart
        dbc.Card([
            dbc.CardHeader([
                html.Span("Phase Timeline", className="me-3"),
                html.Small([
                    html.Span("● ", style={"color": COLORS["purple"]}),
                    html.Span("Waterfall  ", className="text-muted me-2"),
                    html.Span("● ", style={"color": COLORS["yellow"]}),
                    html.Span("Agile  ", className="text-muted me-2"),
                    html.Span("● ", style={"color": COLORS["orange"]}),
                    html.Span("Hybrid", className="text-muted"),
                ]),
            ]),
            dbc.CardBody(
                dcc.Graph(
                    figure=gantt_chart(phases),
                    config={"displayModeBar": False},
                ) if not phases.empty else empty_state("No phase data available.")
            ),
        ], className="chart-card mb-4"),

        # Phase details table
        dbc.Card([
            dbc.CardHeader("Phase Details"),
            dbc.CardBody([
                dbc.Table([
                    html.Thead(html.Tr([
                        html.Th("Phase"),
                        html.Th("Type"),
                        html.Th("Method"),
                        html.Th("Status"),
                        html.Th("Tasks", className="text-center"),
                        html.Th("Progress"),
                    ])),
                    html.Tbody([
                        html.Tr([
                            html.Td(row["name"], className="fw-bold"),
                            html.Td(html.Small(row.get("phase_type", "").title())),
                            html.Td(dbc.Badge(
                                row.get("delivery_method", "N/A").title(),
                                color="info",
                            )),
                            html.Td(dbc.Badge(
                                row.get("status", "").replace("_", " ").title(),
                                color="success" if row.get("status") == "done"
                                else "primary" if row.get("status") == "in_progress"
                                else "secondary",
                            )),
                            html.Td(
                                f"{row.get('done_count', 0)}/{row.get('task_count', 0)}",
                                className="text-center",
                            ),
                            html.Td(
                                dbc.Progress(
                                    value=row.get("pct_complete", 0),
                                    style={"height": "8px"},
                                    color="success",
                                ),
                            ),
                        ])
                        for _, row in phases.iterrows()
                    ]),
                ], bordered=False, hover=True, responsive=True,
                    className="table-dark table-sm"),
            ] if not phases.empty else [empty_state("No phase data.")]),
        ]),

        auto_refresh(),
    ])
