"""
My Work Page
==============
Personal task view with inline status changes and task editing.
"""

import json
import dash
from dash import html, dcc, callback, Input, Output, State, ctx, ALL, no_update
import dash_bootstrap_components as dbc
from services.auth_service import get_user_token, get_user_email
from services import task_service, sprint_service
from components.kpi_card import kpi_card
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from components.crud_modal import (
    crud_modal, get_modal_values, set_field_errors,
    modal_field_states, modal_error_outputs,
)
from components.toast import make_toast_output
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
STATUS_OPTIONS = [
    {"label": "To Do", "value": "todo"},
    {"label": "In Progress", "value": "in_progress"},
    {"label": "Review", "value": "review"},
    {"label": "Done", "value": "done"},
]

TEAM_MEMBER_OPTIONS = [
    {"label": "Cory S.", "value": "u-001"},
    {"label": "Chris J.", "value": "u-002"},
    {"label": "Anna K.", "value": "u-003"},
]

TASK_FIELDS = [
    {"id": "title", "label": "Title", "type": "text", "required": True,
     "placeholder": "Task title"},
    {"id": "task_type", "label": "Type", "type": "select", "required": True,
     "options": [
         {"label": "Epic", "value": "epic"}, {"label": "Story", "value": "story"},
         {"label": "Task", "value": "task"}, {"label": "Bug", "value": "bug"},
         {"label": "Subtask", "value": "subtask"},
     ]},
    {"id": "priority", "label": "Priority", "type": "select", "required": True,
     "options": [
         {"label": "Critical", "value": "critical"}, {"label": "High", "value": "high"},
         {"label": "Medium", "value": "medium"}, {"label": "Low", "value": "low"},
     ]},
    {"id": "story_points", "label": "Story Points", "type": "number",
     "required": False, "min": 0, "max": 100, "placeholder": "0"},
    {"id": "assignee", "label": "Assignee", "type": "select", "required": False,
     "options": TEAM_MEMBER_OPTIONS, "placeholder": "Unassigned"},
    {"id": "description", "label": "Description", "type": "textarea",
     "required": False, "rows": 3, "placeholder": "Task description..."},
]


def _task_item(task):
    """Render a task list item with status dropdown and edit link."""
    task_id = task.get("task_id", "")
    status = task.get("status", "todo")
    priority = task.get("priority", "medium")

    return dbc.ListGroupItem([
        dbc.Row([
            # Title + type
            dbc.Col([
                html.Div([
                    html.Span(
                        "● ",
                        style={"color": PRIORITY_COLORS.get(priority, COLORS["text_muted"])},
                    ),
                    html.A(
                        task.get("title", "Untitled"),
                        id={"type": "my-work-task-edit-btn", "index": task_id},
                        className="fw-bold text-decoration-none",
                        style={"cursor": "pointer", "color": COLORS.get("text", "#fff")},
                    ),
                ]),
                html.Small([
                    dbc.Badge(
                        task.get("task_type", "task").title(),
                        color="secondary", className="me-2",
                    ),
                    html.Span(f"{priority.title()}", className="text-muted"),
                ]),
            ], width=5),
            # Points
            dbc.Col([
                html.Span(f"{task.get('story_points', 0)} pts"),
            ], width=2, className="d-flex align-items-center justify-content-center"),
            # Status dropdown
            dbc.Col([
                dbc.Select(
                    id={"type": "my-work-task-status-dd", "index": task_id},
                    options=STATUS_OPTIONS,
                    value=status,
                    size="sm",
                ),
            ], width=3, className="d-flex align-items-center"),
            # Task ID
            dbc.Col([
                html.Small(task_id, className="text-muted"),
            ], width=2, className="d-flex align-items-center justify-content-end"),
        ], align="center"),
    ], className="bg-transparent border-secondary")


def _build_content():
    """Build the actual page content."""
    token = get_user_token()
    user_email = get_user_email()

    # Get all sprint tasks (in production, filter by current user)
    all_tasks = sprint_service.get_sprint_tasks("sp-004", user_token=token)
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
        html.Div([
            html.Div(html.I(className="bi bi-person-check-fill"), className="page-header-icon"),
            html.H4("My Work", className="page-title"),
        ], className="page-header mb-1"),
        html.P(display_name, className="page-subtitle mb-3",
               style={"color": COLORS["accent"]}),

        # KPI strip
        dbc.Row([
            dbc.Col(kpi_card("My Tasks", total, f"{total_points} points",
                             icon="list-task", icon_color="blue"), width=3),
            dbc.Col(kpi_card("In Progress", in_progress, "active",
                             COLORS["accent"],
                             icon="play-circle-fill", icon_color="yellow"), width=3),
            dbc.Col(kpi_card("In Review", in_review, "awaiting review",
                             COLORS["yellow"],
                             icon="eye-fill", icon_color="purple"), width=3),
            dbc.Col(kpi_card("Done", done,
                             f"{(done / max(total, 1) * 100):.0f}% complete",
                             COLORS["green"],
                             icon="check-circle-fill", icon_color="green"), width=3),
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
    ])


def layout():
    return html.Div([
        # Stores
        dcc.Store(id="my-work-mutation-counter", data=0),
        dcc.Store(id="my-work-selected-task-store", data=None),

        # Content
        html.Div(id="my-work-content"),
        auto_refresh(interval_id="my-work-refresh-interval"),

        # Edit modal (no create, no delete — tasks are created elsewhere)
        crud_modal("my-work-task", "Edit Task", TASK_FIELDS),
    ])


# ── Callbacks ───────────────────────────────────────────────────────


@callback(
    Output("my-work-content", "children"),
    Input("my-work-refresh-interval", "n_intervals"),
    Input("my-work-mutation-counter", "data"),
)
def refresh_my_work(n, mutation_count):
    return _build_content()


@callback(
    Output("my-work-task-modal", "is_open", allow_duplicate=True),
    Output("my-work-task-modal-title", "children", allow_duplicate=True),
    Output("my-work-selected-task-store", "data", allow_duplicate=True),
    Output("my-work-task-title", "value", allow_duplicate=True),
    Output("my-work-task-task_type", "value", allow_duplicate=True),
    Output("my-work-task-priority", "value", allow_duplicate=True),
    Output("my-work-task-story_points", "value", allow_duplicate=True),
    Output("my-work-task-assignee", "value", allow_duplicate=True),
    Output("my-work-task-description", "value", allow_duplicate=True),
    Input({"type": "my-work-task-edit-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_edit_modal(edit_clicks):
    """Open edit modal populated from service."""
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        return (no_update,) * 9

    task_id = triggered["index"]
    token = get_user_token()
    task_df = task_service.get_task(task_id, user_token=token)
    if task_df.empty:
        return (no_update,) * 9

    task = task_df.iloc[0]
    stored = {"task_id": task_id, "updated_at": str(task.get("updated_at", ""))}
    return (
        True, f"Edit Task — {task_id}", json.dumps(stored),
        task.get("title", ""), task.get("task_type"), task.get("priority"),
        task.get("story_points"), task.get("assignee"), task.get("description", ""),
    )


@callback(
    Output("my-work-task-modal", "is_open", allow_duplicate=True),
    Output("my-work-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    *modal_error_outputs("my-work-task", TASK_FIELDS),
    Input("my-work-task-save-btn", "n_clicks"),
    State("my-work-selected-task-store", "data"),
    State("my-work-mutation-counter", "data"),
    *modal_field_states("my-work-task", TASK_FIELDS),
    prevent_initial_call=True,
)
def save_task(n_clicks, stored_task, counter, *field_values):
    """Update a task (edit only)."""
    if not stored_task:
        return (no_update,) * (6 + len(TASK_FIELDS) * 2)

    form_data = get_modal_values("my-work-task", TASK_FIELDS, *field_values)
    stored = json.loads(stored_task) if isinstance(stored_task, str) else stored_task
    task_id = stored["task_id"]
    expected = stored.get("updated_at", "")

    token = get_user_token()
    email = get_user_email()
    result = task_service.update_task_from_form(
        task_id, form_data, expected,
        user_email=email, user_token=token,
    )

    if result["success"]:
        no_errors = set_field_errors("my-work-task", TASK_FIELDS, {})
        error_outputs = []
        for inv, fb in zip(no_errors[0], no_errors[1]):
            error_outputs.extend([inv, fb])
        return (False, (counter or 0) + 1, result["message"], "Success", "success", True,
                *error_outputs)

    errors = result.get("errors", {})
    field_errors = set_field_errors("my-work-task", TASK_FIELDS, errors)
    error_outputs = []
    for inv, fb in zip(field_errors[0], field_errors[1]):
        error_outputs.extend([inv, fb])
    return (True, no_update, result["message"], "Error", "danger", True,
            *error_outputs)


@callback(
    Output("my-work-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input({"type": "my-work-task-status-dd", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def change_status(status_values):
    """Update task status from inline dropdown."""
    triggered = ctx.triggered
    if not triggered or triggered[0]["value"] is None:
        return (no_update,) * 5

    prop_id = triggered[0]["prop_id"]
    try:
        id_dict = json.loads(prop_id.rsplit(".", 1)[0])
        task_id = id_dict["index"]
    except (json.JSONDecodeError, KeyError):
        return (no_update,) * 5

    new_status = triggered[0]["value"]
    token = get_user_token()
    email = get_user_email()

    success = task_service.update_task_status(task_id, new_status, email or "unknown",
                                              user_token=token)
    if success:
        label = STATUS_LABELS.get(new_status, new_status)
        return 1, f"Task moved to {label}", "Status Updated", "success", True
    return no_update, "Failed to update status", "Error", "danger", True


@callback(
    Output("my-work-task-modal", "is_open", allow_duplicate=True),
    Input("my-work-task-cancel-btn", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_edit_modal(n):
    """Close edit modal on cancel."""
    return False
