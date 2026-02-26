"""
Backlog Page
=============
Product backlog with unscheduled tasks, priority ordering, and task details.
"""

import dash
from dash import html, callback, Input, Output
import dash_bootstrap_components as dbc
from services.auth_service import get_user_token
from services.task_service import get_backlog
from components.kpi_card import kpi_card
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from charts.theme import COLORS
from utils.labels import STATUS_LABELS

dash.register_page(__name__, path="/backlog", name="Backlog")

PRIORITY_COLORS = {
    "critical": COLORS["red"], "high": COLORS["orange"],
    "medium": COLORS["yellow"], "low": COLORS["text_muted"],
}


def _backlog_row(task):
    """Render a single backlog task row."""
    priority = task.get("priority", "medium")
    return dbc.ListGroupItem([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Span(
                        "● ",
                        style={"color": PRIORITY_COLORS.get(priority, COLORS["text_muted"])},
                    ),
                    html.Span(task.get("title", "Untitled"), className="fw-bold"),
                ]),
                html.Small([
                    dbc.Badge(
                        task.get("task_type", "task").title(),
                        color="secondary", className="me-2",
                    ),
                    html.Span(
                        f"{priority.title()} priority",
                        className="text-muted",
                    ),
                ]),
            ], width=6),
            dbc.Col([
                html.Div(
                    f"{task.get('story_points', 0)} pts",
                    className="text-center",
                ),
            ], width=2, className="d-flex align-items-center justify-content-center"),
            dbc.Col([
                html.Small(
                    task.get("assignee_name") or "Unassigned",
                    className="text-muted",
                ),
            ], width=2, className="d-flex align-items-center"),
            dbc.Col([
                dbc.Badge(
                    STATUS_LABELS.get(task.get("status", "backlog"), "Backlog"),
                    color="info",
                ),
            ], width=2, className="d-flex align-items-center justify-content-end"),
        ], align="center"),
    ], className="bg-transparent border-secondary")


def _build_content():
    """Build the actual page content."""
    token = get_user_token()
    backlog = get_backlog("prj-001", user_token=token)

    if not backlog.empty:
        total = len(backlog)
        total_points = int(backlog["story_points"].sum())
        unassigned = len(backlog[backlog["assignee_name"].isna() | (backlog["assignee_name"] == "")])
        high_priority = len(backlog[backlog["priority"].isin(["critical", "high"])])
    else:
        total = total_points = unassigned = high_priority = 0

    return html.Div([
        html.H4("Backlog", className="page-title mb-3"),
        html.P(
            "Unscheduled work items awaiting sprint assignment. "
            "Sorted by priority and backlog rank.",
            className="page-subtitle mb-4",
        ),

        # KPI strip
        dbc.Row([
            dbc.Col(kpi_card("Backlog Items", total, "unscheduled"), width=3),
            dbc.Col(kpi_card("Total Points", total_points, "estimated"), width=3),
            dbc.Col(kpi_card("High Priority", high_priority, "critical + high",
                             COLORS["orange"] if high_priority > 0 else None), width=3),
            dbc.Col(kpi_card("Unassigned", unassigned, "need owner",
                             COLORS["yellow"] if unassigned > 0 else None), width=3),
        ], className="kpi-strip mb-4"),

        # Backlog list
        dbc.Card([
            dbc.CardHeader("Backlog Items"),
            dbc.CardBody([
                dbc.ListGroup([
                    _backlog_row(row.to_dict())
                    for _, row in backlog.iterrows()
                ]),
            ] if not backlog.empty else [empty_state("No backlog items.")]),
        ]),
    ])


def layout():
    return html.Div([
        html.Div(id="backlog-content"),
        auto_refresh(interval_id="backlog-refresh-interval"),
    ])


@callback(
    Output("backlog-content", "children"),
    Input("backlog-refresh-interval", "n_intervals"),
)
def refresh_backlog(n):
    return _build_content()
