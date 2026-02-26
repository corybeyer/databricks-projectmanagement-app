"""
My Work Page
==============
Personal task view showing the current user's assigned tasks.
"""

import dash
from dash import html
import dash_bootstrap_components as dbc
from services.auth_service import get_user_token, get_user_email
from services.sprint_service import get_sprint_tasks
from components.kpi_card import kpi_card
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from charts.theme import COLORS
from utils.labels import STATUS_LABELS

dash.register_page(__name__, path="/my-work", name="My Work")

STATUS_COLORS = {
    "todo": "secondary", "in_progress": "primary",
    "review": "info", "done": "success",
}
PRIORITY_COLORS = {
    "critical": COLORS["red"], "high": COLORS["orange"],
    "medium": COLORS["yellow"], "low": COLORS["text_muted"],
}


def _task_item(task):
    """Render a task list item."""
    status = task.get("status", "todo")
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
                    html.Span(f"{priority.title()}", className="text-muted"),
                ]),
            ], width=6),
            dbc.Col([
                html.Span(f"{task.get('story_points', 0)} pts"),
            ], width=2, className="d-flex align-items-center justify-content-center"),
            dbc.Col([
                dbc.Badge(
                    STATUS_LABELS.get(status, status.title()),
                    color=STATUS_COLORS.get(status, "secondary"),
                ),
            ], width=2, className="d-flex align-items-center justify-content-center"),
            dbc.Col([
                html.Small(task.get("task_id", ""), className="text-muted"),
            ], width=2, className="d-flex align-items-center justify-content-end"),
        ], align="center"),
    ], className="bg-transparent border-secondary")


def layout():
    token = get_user_token()
    user_email = get_user_email()

    # Get all sprint tasks (in real app, filter by current user)
    all_tasks = get_sprint_tasks("sp-004", user_token=token)

    # Filter to current user's tasks (sample data uses display names)
    # In production, this would filter by user_id from auth
    my_tasks = all_tasks

    if not my_tasks.empty:
        total = len(my_tasks)
        in_progress = len(my_tasks[my_tasks["status"] == "in_progress"])
        in_review = len(my_tasks[my_tasks["status"] == "review"])
        done = len(my_tasks[my_tasks["status"] == "done"])
        total_points = int(my_tasks["story_points"].sum())
    else:
        total = in_progress = in_review = done = total_points = 0

    display_name = user_email or "Team Member"

    return html.Div([
        html.H4("My Work", className="page-title mb-1"),
        html.P(display_name, className="page-subtitle mb-3",
               style={"color": COLORS["accent"]}),

        # KPI strip
        dbc.Row([
            dbc.Col(kpi_card("My Tasks", total, f"{total_points} points"), width=3),
            dbc.Col(kpi_card("In Progress", in_progress, "active",
                             COLORS["accent"]), width=3),
            dbc.Col(kpi_card("In Review", in_review, "awaiting review",
                             COLORS["yellow"]), width=3),
            dbc.Col(kpi_card("Done", done,
                             f"{(done/max(total,1)*100):.0f}% complete",
                             COLORS["green"]), width=3),
        ], className="kpi-strip mb-4"),

        # Active tasks (not done)
        dbc.Card([
            dbc.CardHeader("Active Tasks"),
            dbc.CardBody([
                dbc.ListGroup([
                    _task_item(row.to_dict())
                    for _, row in my_tasks[my_tasks["status"] != "done"].iterrows()
                ]) if not my_tasks[my_tasks["status"] != "done"].empty
                else empty_state("No active tasks. Nice work!"),
            ]),
        ], className="mb-3"),

        # Completed tasks
        dbc.Card([
            dbc.CardHeader("Completed"),
            dbc.CardBody([
                dbc.ListGroup([
                    _task_item(row.to_dict())
                    for _, row in my_tasks[my_tasks["status"] == "done"].iterrows()
                ]) if not my_tasks[my_tasks["status"] == "done"].empty
                else empty_state("No completed tasks yet."),
            ]),
        ]),

        auto_refresh(),
    ])
