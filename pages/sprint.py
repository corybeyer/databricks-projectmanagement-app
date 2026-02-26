"""
Sprint Board Page
==================
Kanban-style sprint board with velocity and burndown charts.
"""

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
from services.auth_service import get_user_token
from services.sprint_service import get_sprints, get_sprint_tasks
from services.analytics_service import get_velocity, get_burndown
from components.kpi_card import kpi_card
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from charts.theme import COLORS
from charts.sprint_charts import velocity_chart, burndown_chart
from utils.labels import STATUS_LABELS

dash.register_page(__name__, path="/sprint", name="Sprint Board")

KANBAN_COLUMNS = ["todo", "in_progress", "review", "done"]


def _task_card(task):
    """Render a single task card for the kanban board."""
    priority_colors = {
        "critical": COLORS["red"], "high": COLORS["orange"],
        "medium": COLORS["yellow"], "low": COLORS["text_muted"],
    }
    type_icons = {"story": "bookmark-fill", "task": "check-square", "bug": "bug-fill"}
    priority = task.get("priority", "medium")
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(
                    className=f"bi bi-{type_icons.get(task.get('task_type', 'task'), 'check-square')} me-1",
                    style={"color": COLORS["text_muted"], "fontSize": "0.75rem"},
                ),
                html.Small(task.get("task_id", ""), className="text-muted"),
            ], className="d-flex align-items-center mb-1"),
            html.Div(task.get("title", "Untitled"), className="small fw-bold mb-2"),
            html.Div([
                html.Span(
                    f"{task.get('story_points', 0)} pts",
                    className="badge bg-secondary me-2",
                ),
                html.Span(
                    "● ",
                    style={"color": priority_colors.get(priority, COLORS["text_muted"]),
                           "fontSize": "0.6rem"},
                ),
                html.Small(
                    task.get("assignee_name") or "Unassigned",
                    className="text-muted",
                ),
            ], className="d-flex align-items-center"),
        ], className="p-2"),
    ], className="mb-2 bg-transparent border-secondary")


def _kanban_column(status, tasks_df):
    """Render a kanban column with its tasks."""
    column_tasks = tasks_df[tasks_df["status"] == status] if not tasks_df.empty else tasks_df
    count = len(column_tasks)
    points = int(column_tasks["story_points"].sum()) if not column_tasks.empty else 0

    return dbc.Col([
        html.Div([
            html.Div([
                html.Span(STATUS_LABELS.get(status, status.title()), className="fw-bold small"),
                html.Span(f" ({count})", className="text-muted small"),
            ]),
            html.Small(f"{points} pts", className="text-muted"),
        ], className="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom border-secondary"),
        html.Div([
            _task_card(row.to_dict())
            for _, row in column_tasks.iterrows()
        ] if not column_tasks.empty else [
            html.Div("No tasks", className="text-muted small text-center p-3"),
        ]),
    ], width=3)


def _build_content():
    """Build the actual page content."""
    token = get_user_token()
    sprints = get_sprints("prj-001", user_token=token)
    active_sprint = sprints[sprints["status"] == "active"] if not sprints.empty else sprints

    if not active_sprint.empty:
        sprint = active_sprint.iloc[0]
        sprint_id = sprint["sprint_id"]
        sprint_name = sprint["name"]
        tasks = get_sprint_tasks(sprint_id, user_token=token)
        total_pts = int(sprint.get("total_points", 0))
        done_pts = int(sprint.get("done_points", 0))
        capacity = int(sprint.get("capacity_points", 0))
    else:
        sprint_name = "No Active Sprint"
        tasks = get_sprint_tasks("sp-004", user_token=token)
        sprint_id = "sp-004"
        total_pts = done_pts = capacity = 0

    velocity_df = get_velocity("prj-001", user_token=token)
    burndown_df = get_burndown(sprint_id, user_token=token)

    return html.Div([
        html.H4("Sprint Board", className="page-title mb-1"),
        html.P(sprint_name, className="page-subtitle mb-3",
               style={"color": COLORS["accent"]}),

        # Sprint KPIs
        dbc.Row([
            dbc.Col(kpi_card("Total Points", total_pts, f"of {capacity} capacity"), width=3),
            dbc.Col(kpi_card("Completed", done_pts,
                             f"{(done_pts/max(total_pts,1)*100):.0f}% done",
                             COLORS["green"]), width=3),
            dbc.Col(kpi_card("Remaining", total_pts - done_pts,
                             "points left"), width=3),
            dbc.Col(kpi_card("Team Load",
                             f"{(total_pts/max(capacity,1)*100):.0f}%",
                             "of capacity"), width=3),
        ], className="kpi-strip mb-4"),

        # Kanban board
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    _kanban_column(status, tasks)
                    for status in KANBAN_COLUMNS
                ]),
            ]),
        ], className="mb-4"),

        # Charts row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Sprint Velocity"),
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
                    dbc.CardHeader("Sprint Burndown"),
                    dbc.CardBody(
                        dcc.Graph(
                            figure=burndown_chart(burndown_df, sprint_name),
                            config={"displayModeBar": False},
                        ) if not burndown_df.empty else empty_state("No burndown data.")
                    ),
                ], className="chart-card"),
            ], width=6),
        ]),
    ])


def layout():
    return html.Div([
        html.Div(id="sprint-content"),
        auto_refresh(interval_id="sprint-refresh-interval"),
    ])


@callback(
    Output("sprint-content", "children"),
    Input("sprint-refresh-interval", "n_intervals"),
)
def refresh_sprint(n):
    return _build_content()
