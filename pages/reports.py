"""
Reports Page
==============
Analytics dashboard: velocity trends, cycle time analysis, gate status.
"""

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
from services.auth_service import get_user_token
from services.analytics_service import get_velocity, get_cycle_times, get_gate_status
from components.kpi_card import kpi_card
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from charts.theme import COLORS
from charts.sprint_charts import velocity_chart
from charts.analytics_charts import cycle_time_chart
from utils.labels import GATE_LABELS
from components.export_button import export_button

dash.register_page(__name__, path="/reports", name="Reports")


def _gate_row(gate):
    """Render a gate status row."""
    status = gate.get("status", "pending")
    color_map = {
        "approved": "success", "pending": "warning",
        "rejected": "danger", "deferred": "secondary",
    }
    icon_map = {
        "approved": "check-circle-fill", "pending": "clock-fill",
        "rejected": "x-circle-fill", "deferred": "pause-circle-fill",
    }
    return html.Tr([
        html.Td(html.Span(
            f"Gate {gate.get('gate_order', '?')}",
            className="fw-bold",
        )),
        html.Td(gate.get("phase_name", "N/A")),
        html.Td([
            html.I(
                className=f"bi bi-{icon_map.get(status, 'question-circle')} me-1",
                style={"color": COLORS["green"] if status == "approved" else COLORS["yellow"]},
            ),
            dbc.Badge(
                GATE_LABELS.get(status, status.title()),
                color=color_map.get(status, "secondary"),
            ),
        ]),
        html.Td(html.Small(
            gate.get("decided_by") or "—",
            className="text-muted",
        )),
        html.Td(html.Small(
            gate.get("decided_at") or "—",
            className="text-muted",
        )),
    ])


def _build_content(project_id=None):
    """Build the actual page content."""
    token = get_user_token()
    pid = project_id or "prj-001"
    velocity_df = get_velocity(pid, user_token=token)
    cycle_df = get_cycle_times(pid, user_token=token)
    gates_df = get_gate_status(pid, user_token=token)

    # Velocity stats
    if not velocity_df.empty:
        avg_velocity = velocity_df["completed_points"].mean()
        last_velocity = velocity_df["completed_points"].iloc[-1]
        total_delivered = int(velocity_df["completed_points"].sum())
    else:
        avg_velocity = last_velocity = total_delivered = 0

    # Gate stats
    if not gates_df.empty:
        total_gates = len(gates_df)
        approved_gates = len(gates_df[gates_df["status"] == "approved"])
    else:
        total_gates = approved_gates = 0

    return html.Div([
        html.Div([
            html.Div(html.I(className="bi bi-graph-up-arrow"), className="page-header-icon"),
            html.H4("Reports", className="page-title"),
        ], className="page-header mb-3"),
        html.P(
            "Analytics and reporting: velocity trends, cycle time analysis, "
            "and governance gate tracking.",
            className="page-subtitle mb-4",
        ),

        # KPI strip
        dbc.Row([
            dbc.Col(kpi_card("Avg Velocity", f"{avg_velocity:.0f} pts",
                             "per sprint", icon="speedometer2", icon_color="blue"), width=3),
            dbc.Col(kpi_card("Last Sprint", f"{last_velocity:.0f} pts",
                             "delivered", COLORS["green"], icon="lightning-fill", icon_color="purple"), width=3),
            dbc.Col(kpi_card("Total Delivered", total_delivered, "story points", icon="trophy-fill", icon_color="green"), width=3),
            dbc.Col(kpi_card("Gates Passed", f"{approved_gates}/{total_gates}",
                             "approved", icon="shield-check", icon_color="purple"), width=3),
        ], className="kpi-strip mb-4"),

        # Charts row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Velocity Trend"),
                    dbc.CardBody(
                        dcc.Graph(
                            figure=velocity_chart(velocity_df),
                            config={"displayModeBar": False},
                        ) if not velocity_df.empty else empty_state("No velocity data.")
                    ),
                ], className="chart-card"),
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Cycle Time by Status"),
                    dbc.CardBody(
                        dcc.Graph(
                            figure=cycle_time_chart(cycle_df),
                            config={"displayModeBar": False},
                        ) if not cycle_df.empty else empty_state("No cycle time data.")
                    ),
                ], className="chart-card"),
            ], width=6),
        ], className="mb-4"),

        # Gate status table
        dbc.Card([
            dbc.CardHeader("Governance Gates"),
            dbc.CardBody([
                dbc.Table([
                    html.Thead(html.Tr([
                        html.Th("Gate"),
                        html.Th("Phase"),
                        html.Th("Status"),
                        html.Th("Decided By"),
                        html.Th("Date"),
                    ])),
                    html.Tbody([
                        _gate_row(row.to_dict())
                        for _, row in gates_df.iterrows()
                    ]),
                ], bordered=False, hover=True, responsive=True,
                    className="table-dark table-sm"),
            ] if not gates_df.empty else [empty_state("No gate data.")]),
        ]),
    ])


def layout():
    return html.Div([
        dbc.Row([
            dbc.Col(className="flex-grow-1"),
            dbc.Col(export_button("reports-export-btn", "Export"), width="auto"),
        ], className="mb-3"),
        html.Div(id="reports-content"),
        auto_refresh(interval_id="reports-refresh-interval"),
    ])


@callback(
    Output("reports-content", "children"),
    Input("reports-refresh-interval", "n_intervals"),
    Input("active-project-store", "data"),
)
def refresh_reports(n, active_project):
    return _build_content(project_id=active_project)


@callback(
    Output("reports-export-btn-download", "data"),
    Input("reports-export-btn", "n_clicks"),
    prevent_initial_call=True,
)
def export_reports(n_clicks):
    """Export velocity data to Excel."""
    if not n_clicks:
        from dash import no_update
        return no_update
    from datetime import datetime
    from services import export_service
    token = get_user_token()
    df = get_velocity(user_token=token)
    excel_bytes = export_service.to_excel(df, "reports")
    return dcc.send_bytes(excel_bytes, f"reports_{datetime.now().strftime('%Y%m%d')}.xlsx")
