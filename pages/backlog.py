"""
Backlog Page
=============
Product backlog with task CRUD, priority ordering, and move-to-sprint.
"""

import json
import dash
from dash import html, dcc, callback, Input, Output, State, ctx, ALL, no_update
import dash_bootstrap_components as dbc
from services.auth_service import (
    get_user_token, get_user_email, get_current_user, has_permission,
)
from services import task_service, sprint_service
from components.kpi_card import kpi_card
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from components.crud_modal import (
    crud_modal, confirm_delete_modal, get_modal_values,
    set_field_errors, modal_field_states, modal_error_outputs,
)
from components.toast import make_toast_output
from charts.theme import COLORS
from utils.labels import STATUS_LABELS
from components.filter_bar import filter_bar
from components.export_button import export_button

dash.register_page(__name__, path="/backlog", name="Backlog")

PRIORITY_COLORS = {
    "critical": COLORS["red"], "high": COLORS["orange"],
    "medium": COLORS["yellow"], "low": COLORS["text_muted"],
}

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


def _get_sprint_options():
    """Fetch active/planning sprints for move-to-sprint dropdown."""
    token = get_user_token()
    sprints = sprint_service.get_sprints("prj-001", user_token=token)
    if sprints.empty:
        return []
    active = sprints[sprints["status"].isin(["active", "planning"])]
    return [
        {"label": row["name"], "value": row["sprint_id"]}
        for _, row in active.iterrows()
    ]


def _backlog_row(task, sprint_options):
    """Render a single backlog task row with edit, move, and delete."""
    task_id = task.get("task_id", "")
    priority = task.get("priority", "medium")

    return dbc.ListGroupItem([
        dbc.Row([
            # Title + type badge
            dbc.Col([
                html.Div([
                    html.Span(
                        "● ",
                        style={"color": PRIORITY_COLORS.get(priority, COLORS["text_muted"])},
                    ),
                    html.A(
                        task.get("title", "Untitled"),
                        id={"type": "backlog-task-edit-btn", "index": task_id},
                        className="fw-bold text-decoration-none",
                        style={"cursor": "pointer", "color": COLORS.get("text", "#fff")},
                    ),
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
            ], width=4),
            # Points
            dbc.Col([
                html.Div(
                    f"{task.get('story_points', 0)} pts",
                    className="text-center",
                ),
            ], width=1, className="d-flex align-items-center justify-content-center"),
            # Assignee
            dbc.Col([
                html.Small(
                    task.get("assignee_name") or "Unassigned",
                    className="text-muted",
                ),
            ], width=2, className="d-flex align-items-center"),
            # Move to sprint
            dbc.Col([
                dbc.Select(
                    id={"type": "backlog-task-sprint-dd", "index": task_id},
                    options=sprint_options,
                    placeholder="Move to sprint...",
                    size="sm",
                ) if sprint_options else html.Small("No sprints", className="text-muted"),
            ], width=3, className="d-flex align-items-center"),
            # Actions
            dbc.Col([
                dbc.Button(
                    html.I(className="bi bi-trash"),
                    id={"type": "backlog-task-delete-btn", "index": task_id},
                    size="sm", color="link", className="p-0 text-muted",
                ),
            ], width=2, className="d-flex align-items-center justify-content-end"),
        ], align="center"),
    ], className="bg-transparent border-secondary")


def _build_content(project_id=None, status_filter=None, priority_filter=None,
                   assignee_filter=None, type_filter=None):
    """Build the actual page content."""
    token = get_user_token()
    pid = project_id or "prj-001"
    backlog = task_service.get_backlog(pid, user_token=token)
    sprint_options = _get_sprint_options()

    # Filter to backlog items (sprint_id is null)
    if not backlog.empty and "sprint_id" in backlog.columns:
        backlog = backlog[backlog["sprint_id"].isna() | (backlog["sprint_id"] == "")]

    # Apply filters
    if not backlog.empty and status_filter:
        backlog = backlog[backlog["status"].isin(status_filter)]
    if not backlog.empty and priority_filter:
        backlog = backlog[backlog["priority"].isin(priority_filter)]
    if not backlog.empty and assignee_filter and "assignee" in backlog.columns:
        backlog = backlog[backlog["assignee"].isin(assignee_filter)]
    if not backlog.empty and type_filter and "task_type" in backlog.columns:
        backlog = backlog[backlog["task_type"].isin(type_filter)]

    if not backlog.empty:
        total = len(backlog)
        total_points = int(backlog["story_points"].sum())
        unassigned = len(backlog[
            backlog["assignee_name"].isna() | (backlog["assignee_name"] == "")
        ]) if "assignee_name" in backlog.columns else 0
        high_priority = len(backlog[backlog["priority"].isin(["critical", "high"])])
    else:
        total = total_points = unassigned = high_priority = 0

    return html.Div([
        html.Div([
            html.Div(html.I(className="bi bi-list-check"), className="page-header-icon"),
            html.H4("Backlog", className="page-title"),
        ], className="page-header mb-3"),
        html.P(
            "Unscheduled work items awaiting sprint assignment. "
            "Sorted by priority and backlog rank.",
            className="page-subtitle mb-4",
        ),

        # KPI strip
        dbc.Row([
            dbc.Col(kpi_card("Backlog Items", total, "unscheduled", icon="inbox-fill", icon_color="blue"), width=3),
            dbc.Col(kpi_card("Total Points", total_points, "estimated", icon="lightning-fill", icon_color="purple"), width=3),
            dbc.Col(kpi_card("High Priority", high_priority, "critical + high",
                             COLORS["orange"] if high_priority > 0 else None, icon="exclamation-triangle-fill", icon_color="red"), width=3),
            dbc.Col(kpi_card("Unassigned", unassigned, "need owner",
                             COLORS["yellow"] if unassigned > 0 else None, icon="person-dash-fill", icon_color="yellow"), width=3),
        ], className="kpi-strip mb-4"),

        # Backlog list
        dbc.Card([
            dbc.CardHeader("Backlog Items"),
            dbc.CardBody([
                dbc.ListGroup([
                    _backlog_row(row.to_dict(), sprint_options)
                    for _, row in backlog.iterrows()
                ]),
            ] if not backlog.empty else [empty_state("No backlog items.")]),
        ]),
    ])


BACKLOG_FILTERS = [
    {"id": "status", "label": "Status", "type": "select", "multi": True,
     "options": [{"label": "Backlog", "value": "backlog"},
                 {"label": "To Do", "value": "todo"},
                 {"label": "In Progress", "value": "in_progress"},
                 {"label": "Done", "value": "done"}]},
    {"id": "priority", "label": "Priority", "type": "select", "multi": True,
     "options": [{"label": "Critical", "value": "critical"},
                 {"label": "High", "value": "high"},
                 {"label": "Medium", "value": "medium"},
                 {"label": "Low", "value": "low"}]},
    {"id": "assignee", "label": "Assignee", "type": "select", "multi": True,
     "options": TEAM_MEMBER_OPTIONS},
    {"id": "type", "label": "Type", "type": "select", "multi": True,
     "options": [{"label": "Epic", "value": "epic"},
                 {"label": "Story", "value": "story"},
                 {"label": "Task", "value": "task"},
                 {"label": "Bug", "value": "bug"},
                 {"label": "Subtask", "value": "subtask"}]},
]


def layout():
    user = get_current_user()
    can_write = has_permission(user, "create", "task")
    return html.Div([
        # Stores
        dcc.Store(id="backlog-mutation-counter", data=0),
        dcc.Store(id="backlog-selected-task-store", data=None),

        # Toolbar
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    [html.I(className="bi bi-plus-circle me-1"), "Add Task"],
                    id="backlog-add-task-btn", color="primary", size="sm",
                    style={"display": "inline-block" if can_write else "none"},
                    className="me-2",
                ),
                export_button("backlog-export-btn", "Export"),
            ], className="d-flex justify-content-end mb-3"),
        ]),

        # Filters
        filter_bar("backlog", BACKLOG_FILTERS),

        # Content
        html.Div(id="backlog-content"),
        auto_refresh(interval_id="backlog-refresh-interval"),

        # Modals
        crud_modal("backlog-task", "Create Task", TASK_FIELDS),
        confirm_delete_modal("backlog-task", "task"),
    ])


# ── Callbacks ───────────────────────────────────────────────────────


@callback(
    Output("backlog-content", "children"),
    Input("backlog-refresh-interval", "n_intervals"),
    Input("backlog-mutation-counter", "data"),
    Input("active-project-store", "data"),
    Input("backlog-status-filter", "value"),
    Input("backlog-priority-filter", "value"),
    Input("backlog-assignee-filter", "value"),
    Input("backlog-type-filter", "value"),
)
def refresh_backlog(n, mutation_count, active_project, status_filter,
                    priority_filter, assignee_filter, type_filter):
    return _build_content(
        project_id=active_project,
        status_filter=status_filter,
        priority_filter=priority_filter,
        assignee_filter=assignee_filter,
        type_filter=type_filter,
    )


@callback(
    Output("backlog-task-modal", "is_open", allow_duplicate=True),
    Output("backlog-task-modal-title", "children", allow_duplicate=True),
    Output("backlog-selected-task-store", "data", allow_duplicate=True),
    Output("backlog-task-title", "value", allow_duplicate=True),
    Output("backlog-task-task_type", "value", allow_duplicate=True),
    Output("backlog-task-priority", "value", allow_duplicate=True),
    Output("backlog-task-story_points", "value", allow_duplicate=True),
    Output("backlog-task-assignee", "value", allow_duplicate=True),
    Output("backlog-task-description", "value", allow_duplicate=True),
    Input("backlog-add-task-btn", "n_clicks"),
    Input({"type": "backlog-task-edit-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def toggle_task_modal(add_clicks, edit_clicks):
    """Open task modal for create (blank) or edit (populated)."""
    triggered = ctx.triggered_id

    if triggered == "backlog-add-task-btn":
        return True, "Create Backlog Task", None, "", None, None, None, None, ""

    if isinstance(triggered, dict) and triggered.get("type") == "backlog-task-edit-btn":
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

    return (no_update,) * 9


@callback(
    Output("backlog-task-modal", "is_open", allow_duplicate=True),
    Output("backlog-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    *modal_error_outputs("backlog-task", TASK_FIELDS),
    Input("backlog-task-save-btn", "n_clicks"),
    State("backlog-selected-task-store", "data"),
    State("backlog-mutation-counter", "data"),
    State("active-project-store", "data"),
    *modal_field_states("backlog-task", TASK_FIELDS),
    prevent_initial_call=True,
)
def save_task(n_clicks, stored_task, counter, active_project, *field_values):
    """Save (create or update) a backlog task."""
    form_data = get_modal_values("backlog-task", TASK_FIELDS, *field_values)
    form_data["status"] = "backlog"
    form_data["sprint_id"] = None
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
        no_errors = set_field_errors("backlog-task", TASK_FIELDS, {})
        error_outputs = []
        for inv, fb in zip(no_errors[0], no_errors[1]):
            error_outputs.extend([inv, fb])
        return (False, (counter or 0) + 1, result["message"], "Success", "success", True,
                *error_outputs)

    errors = result.get("errors", {})
    field_errors = set_field_errors("backlog-task", TASK_FIELDS, errors)
    error_outputs = []
    for inv, fb in zip(field_errors[0], field_errors[1]):
        error_outputs.extend([inv, fb])
    return (True, no_update, result["message"], "Error", "danger", True,
            *error_outputs)


@callback(
    Output("backlog-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input({"type": "backlog-task-sprint-dd", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def move_to_sprint(sprint_values):
    """Move a backlog task to a sprint."""
    triggered = ctx.triggered
    if not triggered or triggered[0]["value"] is None:
        return (no_update,) * 5

    prop_id = triggered[0]["prop_id"]
    try:
        id_dict = json.loads(prop_id.rsplit(".", 1)[0])
        task_id = id_dict["index"]
    except (json.JSONDecodeError, KeyError):
        return (no_update,) * 5

    sprint_id = triggered[0]["value"]
    token = get_user_token()
    success = task_service.move_task_to_sprint(task_id, sprint_id, user_token=token)

    if success:
        return 1, "Task moved to sprint", "Moved", "success", True
    return no_update, "Failed to move task", "Error", "danger", True


@callback(
    Output("backlog-task-delete-modal", "is_open", allow_duplicate=True),
    Output("backlog-task-delete-target-store", "data", allow_duplicate=True),
    Input({"type": "backlog-task-delete-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_delete_modal(n_clicks_list):
    """Open delete confirmation."""
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        return no_update, no_update
    return True, triggered["index"]


@callback(
    Output("backlog-task-delete-modal", "is_open", allow_duplicate=True),
    Output("backlog-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input("backlog-task-delete-confirm-btn", "n_clicks"),
    State("backlog-task-delete-target-store", "data"),
    State("backlog-mutation-counter", "data"),
    prevent_initial_call=True,
)
def confirm_delete(n_clicks, task_id, counter):
    """Soft-delete the task."""
    if not task_id:
        return (no_update,) * 6

    token = get_user_token()
    email = get_user_email()
    success = task_service.delete_task(task_id, user_email=email, user_token=token)

    if success:
        return False, (counter or 0) + 1, "Task deleted", "Deleted", "success", True
    return False, no_update, "Failed to delete task", "Error", "danger", True


@callback(
    Output("backlog-task-modal", "is_open", allow_duplicate=True),
    Input("backlog-task-cancel-btn", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_task_modal(n):
    """Close task modal on cancel."""
    return False


@callback(
    Output("backlog-export-btn-download", "data"),
    Input("backlog-export-btn", "n_clicks"),
    prevent_initial_call=True,
)
def export_backlog(n_clicks):
    """Export backlog data to Excel."""
    if not n_clicks:
        return no_update
    from datetime import datetime
    from services import export_service
    token = get_user_token()
    df = task_service.get_backlog(user_token=token)
    excel_bytes = export_service.to_excel(df, "backlog")
    return dcc.send_bytes(excel_bytes, f"backlog_{datetime.now().strftime('%Y%m%d')}.xlsx")
