"""
Sprint Board Page
==================
Kanban-style sprint board with task CRUD, sprint management, and charts.
"""

import json
import dash
from dash import html, dcc, callback, Input, Output, State, ctx, ALL, no_update
import dash_bootstrap_components as dbc
from services.auth_service import get_user_token, get_user_email, get_current_user, has_permission
from services import task_service, sprint_service
from services.analytics_service import get_velocity, get_burndown
from components.kpi_card import kpi_card
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from components.crud_modal import (
    crud_modal, confirm_delete_modal, get_modal_values,
    set_field_errors, modal_field_states, modal_error_outputs,
)
from components.toast import make_toast_output
from charts.theme import COLORS
from charts.sprint_charts import velocity_chart, burndown_chart
from utils.labels import STATUS_LABELS

dash.register_page(__name__, path="/sprint", name="Sprint Board")

KANBAN_COLUMNS = ["todo", "in_progress", "review", "done"]
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

SPRINT_FIELDS = [
    {"id": "name", "label": "Sprint Name", "type": "text", "required": True,
     "placeholder": "Sprint 5"},
    {"id": "goal", "label": "Sprint Goal", "type": "textarea", "required": False,
     "rows": 2, "placeholder": "What is the goal?"},
    {"id": "start_date", "label": "Start Date", "type": "date", "required": True},
    {"id": "end_date", "label": "End Date", "type": "date", "required": True},
    {"id": "capacity_points", "label": "Capacity", "type": "number",
     "required": False, "min": 0, "max": 999, "placeholder": "0"},
]


# ── Helper functions ────────────────────────────────────────────────


def _task_card(task):
    """Render a single task card with status dropdown, edit, and delete."""
    task_id = task.get("task_id", "")
    priority_colors = {
        "critical": COLORS["red"], "high": COLORS["orange"],
        "medium": COLORS["yellow"], "low": COLORS["text_muted"],
    }
    type_icons = {
        "story": "bookmark-fill", "task": "check-square",
        "bug": "bug-fill", "epic": "lightning-fill", "subtask": "diagram-3",
    }
    priority = task.get("priority", "medium")
    status = task.get("status", "todo")

    return dbc.Card([
        dbc.CardBody([
            # Header row: type icon + task ID + action buttons
            html.Div([
                html.Div([
                    html.I(
                        className=f"bi bi-{type_icons.get(task.get('task_type', 'task'), 'check-square')} me-1",
                        style={"color": COLORS["text_muted"], "fontSize": "0.75rem"},
                    ),
                    html.Small(task_id, className="text-muted"),
                ], className="d-flex align-items-center"),
                html.Div([
                    dbc.Button(
                        html.I(className="bi bi-pencil-square"),
                        id={"type": "sprint-task-edit-btn", "index": task_id},
                        size="sm", color="link", className="p-0 me-2 text-muted",
                    ),
                    dbc.Button(
                        html.I(className="bi bi-trash"),
                        id={"type": "sprint-task-delete-btn", "index": task_id},
                        size="sm", color="link", className="p-0 text-muted",
                    ),
                ], className="d-flex align-items-center"),
            ], className="d-flex justify-content-between align-items-center mb-1"),

            # Title
            html.Div(task.get("title", "Untitled"), className="small fw-bold mb-2"),

            # Bottom row: points, priority dot, assignee
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
            ], className="d-flex align-items-center mb-2"),

            # Status dropdown
            dbc.Select(
                id={"type": "sprint-task-status-dd", "index": task_id},
                options=STATUS_OPTIONS,
                value=status,
                size="sm",
            ),
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


def _build_content(sprint_id=None, project_id=None):
    """Build the sprint board content for a given sprint."""
    token = get_user_token()
    pid = project_id or "prj-001"
    sprints = sprint_service.get_sprints(pid, user_token=token)

    # Determine which sprint to show
    if sprint_id and not sprints.empty:
        selected = sprints[sprints["sprint_id"] == sprint_id]
        if selected.empty:
            selected = sprints[sprints["status"] == "active"]
    else:
        selected = sprints[sprints["status"] == "active"] if not sprints.empty else sprints

    if not selected.empty:
        sprint = selected.iloc[0]
        sid = sprint["sprint_id"]
        sprint_name = sprint["name"]
        tasks = sprint_service.get_sprint_tasks(sid, user_token=token)
        total_pts = int(sprint.get("total_points", 0) or 0)
        done_pts = int(sprint.get("done_points", 0) or 0)
        capacity = int(sprint.get("capacity_points", 0) or 0)
    else:
        sprint_name = "No Active Sprint"
        sid = "sp-004"
        tasks = sprint_service.get_sprint_tasks(sid, user_token=token)
        total_pts = done_pts = capacity = 0

    velocity_df = get_velocity(pid, user_token=token)
    burndown_df = get_burndown(sid, user_token=token)

    return html.Div([
        html.Div([
            html.Div(html.I(className="bi bi-view-stacked"), className="page-header-icon"),
            html.H4("Sprint Board", className="page-title"),
        ], className="page-header mb-1"),
        html.P(sprint_name, className="page-subtitle mb-3",
               style={"color": COLORS["accent"]}),

        # Sprint KPIs
        dbc.Row([
            dbc.Col(kpi_card("Total Points", total_pts,
                             f"of {capacity} capacity",
                             icon="lightning-fill", icon_color="blue"), width=3),
            dbc.Col(kpi_card("Completed", done_pts,
                             f"{(done_pts / max(total_pts, 1) * 100):.0f}% done",
                             COLORS["green"],
                             icon="check-circle-fill", icon_color="green"), width=3),
            dbc.Col(kpi_card("Remaining", total_pts - done_pts,
                             "points left",
                             icon="hourglass-split", icon_color="yellow"), width=3),
            dbc.Col(kpi_card("Team Load",
                             f"{(total_pts / max(capacity, 1) * 100):.0f}%",
                             "of capacity",
                             icon="people-fill", icon_color="purple"), width=3),
        ], className="kpi-strip mb-4"),

        # Kanban board
        dbc.Card([
            dbc.CardBody([
                dbc.Row([_kanban_column(status, tasks) for status in KANBAN_COLUMNS]),
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


# ── Layout ──────────────────────────────────────────────────────────


def layout():
    user = get_current_user()
    can_write_task = has_permission(user, "create", "task")
    can_write_sprint = has_permission(user, "create", "sprint")
    return html.Div([
        # Stores
        dcc.Store(id="sprint-mutation-counter", data=0),
        dcc.Store(id="sprint-selected-task-store", data=None),

        # Toolbar row
        dbc.Row([
            dbc.Col([
                dbc.Select(
                    id="sprint-selector",
                    placeholder="Select sprint...",
                    className="mb-2",
                ),
            ], width=4),
            dbc.Col([
                dbc.Button(
                    [html.I(className="bi bi-plus-circle me-1"), "Add Task"],
                    id="sprint-add-task-btn", color="primary", size="sm",
                    className="me-2",
                    style={"display": "inline-block" if can_write_task else "none"},
                ),
                dbc.Button(
                    [html.I(className="bi bi-calendar-plus me-1"), "New Sprint"],
                    id="sprint-new-sprint-btn", color="secondary", size="sm",
                    outline=True, className="me-2",
                    style={"display": "inline-block" if can_write_sprint else "none"},
                ),
                dbc.Button(
                    [html.I(className="bi bi-check-circle me-1"), "Close Sprint"],
                    id="sprint-close-sprint-btn", color="warning", size="sm",
                    outline=True,
                    style={"display": "inline-block" if can_write_sprint else "none"},
                ),
            ], width=8, className="d-flex align-items-start justify-content-end"),
        ], className="mb-3"),

        # Content area
        html.Div(id="sprint-content"),
        auto_refresh(interval_id="sprint-refresh-interval"),

        # Modals
        crud_modal("sprint-task", "Create Task", TASK_FIELDS),
        confirm_delete_modal("sprint-task", "task"),
        crud_modal("sprint-sprint", "Create Sprint", SPRINT_FIELDS),
    ])


# ── Callbacks ───────────────────────────────────────────────────────


@callback(
    Output("sprint-selector", "options"),
    Output("sprint-selector", "value"),
    Input("sprint-refresh-interval", "n_intervals"),
    Input("active-project-store", "data"),
)
def populate_sprint_selector(n, active_project):
    """Load sprint options on page visit."""
    token = get_user_token()
    pid = active_project or "prj-001"
    sprints = sprint_service.get_sprints(pid, user_token=token)
    if sprints.empty:
        return [], None

    options = [
        {"label": f"{row['name']} ({row['status']})", "value": row["sprint_id"]}
        for _, row in sprints.iterrows()
    ]
    active = sprints[sprints["status"] == "active"]
    default_val = active.iloc[0]["sprint_id"] if not active.empty else sprints.iloc[0]["sprint_id"]
    return options, default_val


@callback(
    Output("sprint-content", "children"),
    Input("sprint-refresh-interval", "n_intervals"),
    Input("sprint-mutation-counter", "data"),
    Input("sprint-selector", "value"),
    Input("active-project-store", "data"),
)
def refresh_sprint(n, mutation_count, selected_sprint, active_project):
    """Refresh sprint content on interval, mutation, or sprint selection."""
    return _build_content(sprint_id=selected_sprint, project_id=active_project)


@callback(
    Output("sprint-task-modal", "is_open", allow_duplicate=True),
    Output("sprint-task-modal-title", "children", allow_duplicate=True),
    Output("sprint-selected-task-store", "data", allow_duplicate=True),
    Output("sprint-task-title", "value", allow_duplicate=True),
    Output("sprint-task-task_type", "value", allow_duplicate=True),
    Output("sprint-task-priority", "value", allow_duplicate=True),
    Output("sprint-task-story_points", "value", allow_duplicate=True),
    Output("sprint-task-assignee", "value", allow_duplicate=True),
    Output("sprint-task-description", "value", allow_duplicate=True),
    Input("sprint-add-task-btn", "n_clicks"),
    Input({"type": "sprint-task-edit-btn", "index": ALL}, "n_clicks"),
    State("sprint-selector", "value"),
    prevent_initial_call=True,
)
def toggle_task_modal(add_clicks, edit_clicks, selected_sprint):
    """Open task modal for create (blank) or edit (populated)."""
    # Guard: only proceed if an actual click triggered this callback
    triggered = ctx.triggered
    if not triggered or all(t.get("value") is None or t.get("value") == 0
                           for t in triggered):
        return (no_update,) * 9

    triggered_id = ctx.triggered_id

    if triggered_id == "sprint-add-task-btn" and add_clicks:
        return True, "Create Task", None, "", None, None, None, None, ""

    # Edit mode — pattern-match button
    if isinstance(triggered_id, dict) and triggered_id.get("type") == "sprint-task-edit-btn":
        task_id = triggered["index"]
        token = get_user_token()
        task_df = task_service.get_task(task_id, user_token=token)
        if task_df.empty:
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        task = task_df.iloc[0]
        stored = {"task_id": task_id, "updated_at": str(task.get("updated_at", ""))}
        return (
            True, f"Edit Task — {task_id}", json.dumps(stored),
            task.get("title", ""), task.get("task_type"), task.get("priority"),
            task.get("story_points"), task.get("assignee"), task.get("description", ""),
        )

    return (no_update,) * 9


@callback(
    Output("sprint-task-modal", "is_open", allow_duplicate=True),
    Output("sprint-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    *modal_error_outputs("sprint-task", TASK_FIELDS),
    Input("sprint-task-save-btn", "n_clicks"),
    State("sprint-selected-task-store", "data"),
    State("sprint-selector", "value"),
    State("sprint-mutation-counter", "data"),
    State("active-project-store", "data"),
    *modal_field_states("sprint-task", TASK_FIELDS),
    prevent_initial_call=True,
)
def save_task(n_clicks, stored_task, selected_sprint, counter, active_project, *field_values):
    """Save (create or update) a task."""
    if not n_clicks:
        return (no_update,) * (6 + len(TASK_FIELDS) * 2)
    form_data = get_modal_values("sprint-task", TASK_FIELDS, *field_values)
    form_data["sprint_id"] = selected_sprint
    form_data["project_id"] = active_project or "prj-001"

    token = get_user_token()
    email = get_user_email()

    if stored_task:
        stored = json.loads(stored_task) if isinstance(stored_task, str) else stored_task
        task_id = stored["task_id"]
        expected = stored.get("updated_at", "")
        result = task_service.update_task_from_form(
            task_id, form_data, expected,
            user_email=email, user_token=token,
        )
    else:
        result = task_service.create_task_from_form(
            form_data, user_email=email, user_token=token,
        )

    if result["success"]:
        no_errors = set_field_errors("sprint-task", TASK_FIELDS, {})
        error_outputs = []
        for inv, fb in zip(no_errors[0], no_errors[1]):
            error_outputs.extend([inv, fb])
        return (False, (counter or 0) + 1, result["message"], "Success", "success", True,
                *error_outputs)

    errors = result.get("errors", {})
    field_errors = set_field_errors("sprint-task", TASK_FIELDS, errors)
    error_outputs = []
    for inv, fb in zip(field_errors[0], field_errors[1]):
        error_outputs.extend([inv, fb])
    return (True, no_update, result["message"], "Error", "danger", True,
            *error_outputs)


@callback(
    Output("sprint-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input({"type": "sprint-task-status-dd", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def change_task_status(status_values):
    """Update task status when dropdown changes."""
    triggered = ctx.triggered
    if not triggered or triggered[0]["value"] is None:
        return (no_update,) * 5

    prop_id = triggered[0]["prop_id"]
    # Parse the pattern-matching ID
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
    counter = 1  # Will be added to current
    if success:
        label = STATUS_LABELS.get(new_status, new_status)
        return counter, f"Task moved to {label}", "Status Updated", "success", True
    return no_update, "Failed to update status", "Error", "danger", True


@callback(
    Output("sprint-task-delete-modal", "is_open", allow_duplicate=True),
    Output("sprint-task-delete-target-store", "data", allow_duplicate=True),
    Input({"type": "sprint-task-delete-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_delete_modal(n_clicks_list):
    """Open delete confirmation with the task ID."""
    if not any(n_clicks_list or []):
        return no_update, no_update
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        return no_update, no_update
    task_id = triggered["index"]
    return True, task_id


@callback(
    Output("sprint-task-delete-modal", "is_open", allow_duplicate=True),
    Output("sprint-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input("sprint-task-delete-confirm-btn", "n_clicks"),
    State("sprint-task-delete-target-store", "data"),
    State("sprint-mutation-counter", "data"),
    prevent_initial_call=True,
)
def confirm_delete_task(n_clicks, task_id, counter):
    """Soft-delete the task."""
    if not task_id:
        return no_update, no_update, no_update, no_update, no_update, no_update

    token = get_user_token()
    email = get_user_email()
    success = task_service.delete_task(task_id, user_email=email, user_token=token)

    if success:
        return False, (counter or 0) + 1, "Task deleted", "Deleted", "success", True
    return False, no_update, "Failed to delete task", "Error", "danger", True


@callback(
    Output("sprint-task-modal", "is_open", allow_duplicate=True),
    Input("sprint-task-cancel-btn", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_task_modal(n):
    """Close task modal on cancel."""
    return False


@callback(
    Output("sprint-sprint-modal", "is_open", allow_duplicate=True),
    Input("sprint-new-sprint-btn", "n_clicks"),
    Input("sprint-sprint-cancel-btn", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_sprint_modal(new_clicks, cancel_clicks):
    """Open/close sprint creation modal."""
    triggered = ctx.triggered
    if not triggered or triggered[0].get("value") is None:
        return no_update
    if ctx.triggered_id == "sprint-new-sprint-btn" and new_clicks:
        return True
    return False


@callback(
    Output("sprint-sprint-modal", "is_open", allow_duplicate=True),
    Output("sprint-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    *modal_error_outputs("sprint-sprint", SPRINT_FIELDS),
    Input("sprint-sprint-save-btn", "n_clicks"),
    State("sprint-mutation-counter", "data"),
    State("active-project-store", "data"),
    *modal_field_states("sprint-sprint", SPRINT_FIELDS),
    prevent_initial_call=True,
)
def save_sprint(n_clicks, counter, active_project, *field_values):
    """Create a new sprint."""
    if not n_clicks:
        return (no_update,) * (6 + len(SPRINT_FIELDS) * 2)
    form_data = get_modal_values("sprint-sprint", SPRINT_FIELDS, *field_values)
    form_data["project_id"] = active_project or "prj-001"

    token = get_user_token()
    email = get_user_email()
    result = sprint_service.create_sprint_from_form(
        form_data, user_email=email, user_token=token,
    )

    if result["success"]:
        no_errors = set_field_errors("sprint-sprint", SPRINT_FIELDS, {})
        error_outputs = []
        for inv, fb in zip(no_errors[0], no_errors[1]):
            error_outputs.extend([inv, fb])
        return (False, (counter or 0) + 1, result["message"], "Success", "success", True,
                *error_outputs)

    errors = result.get("errors", {})
    field_errors = set_field_errors("sprint-sprint", SPRINT_FIELDS, errors)
    error_outputs = []
    for inv, fb in zip(field_errors[0], field_errors[1]):
        error_outputs.extend([inv, fb])
    return (True, no_update, result["message"], "Error", "danger", True,
            *error_outputs)


@callback(
    Output("sprint-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input("sprint-close-sprint-btn", "n_clicks"),
    State("sprint-selector", "value"),
    State("sprint-mutation-counter", "data"),
    prevent_initial_call=True,
)
def close_current_sprint(n_clicks, sprint_id, counter):
    """Close the currently selected sprint."""
    if not sprint_id:
        return no_update, "No sprint selected", "Error", "danger", True

    token = get_user_token()
    email = get_user_email()
    result = sprint_service.close_sprint(sprint_id, user_email=email, user_token=token)

    if result["success"]:
        return (counter or 0) + 1, "Sprint closed", "Success", "success", True
    return no_update, result["message"], "Error", "danger", True
