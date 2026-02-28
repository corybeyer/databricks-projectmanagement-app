"""
Task Comments Page — Collaboration & Discussion
=================================================
Standalone comments page for task-level discussions.
Task selector, comment thread, KPI cards, full CRUD on own comments.
"""

import json
from datetime import date

import dash
from dash import html, dcc, callback, Input, Output, State, ctx, ALL, no_update
import dash_bootstrap_components as dbc
from services.auth_service import (
    get_user_token, get_user_email, get_current_user, has_permission,
)
from services import comment_service, task_service
from components.kpi_card import kpi_card
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from components.comment_thread import (
    comment_thread, comment_list_display,
)
from components.crud_modal import confirm_delete_modal
from charts.theme import COLORS

dash.register_page(__name__, path="/comments", name="Task Comments")


# ── Layout ──────────────────────────────────────────────────────────


def layout():
    user = get_current_user()
    _can_write = has_permission(user, "create", "comment")  # noqa: F841
    return html.Div([
        # Stores
        dcc.Store(id="comments-mutation-counter", data=0),
        dcc.Store(id="comments-edit-store", data=None),

        # Page header
        html.Div([
            html.Div(html.I(className="bi bi-chat-dots"), className="page-header-icon"),
            html.H4("Task Comments", className="page-title"),
        ], className="page-header mb-1"),
        html.P(
            "Collaborate on tasks with threaded comments. "
            "Select a task to view and add discussion.",
            className="page-subtitle mb-4",
        ),

        # Task selector row
        dbc.Row([
            dbc.Col([
                dbc.Label("Select Task", className="fw-bold small mb-1"),
                dcc.Dropdown(
                    id="comments-task-selector",
                    placeholder="Choose a task...",
                    className="dash-dropdown-dark",
                ),
            ], md=6),
        ], className="mb-4"),

        # KPI strip
        html.Div(id="comments-kpi-strip", className="mb-4"),

        # Main content: comment thread
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Span("Discussion", className="fw-bold"),
                        html.Span(
                            id="comments-count-badge",
                            className="ms-2",
                        ),
                    ]),
                    dbc.CardBody([
                        html.Div(id="comments-thread-area"),
                    ]),
                ], className="chart-card"),
            ], md=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Task Details"),
                    dbc.CardBody(id="comments-task-detail"),
                ], className="chart-card"),
            ], md=4),
        ]),

        auto_refresh(interval_id="comments-refresh-interval"),

        # Edit comment modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Edit Comment")),
            dbc.ModalBody([
                dbc.Textarea(
                    id="comments-edit-body",
                    rows=4,
                    className="mb-2",
                ),
                dbc.FormFeedback(
                    id="comments-edit-body-feedback",
                    type="invalid",
                ),
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="comments-edit-cancel-btn",
                           color="secondary", outline=True),
                dbc.Button("Save", id="comments-edit-save-btn",
                           color="primary"),
            ]),
        ], id="comments-edit-modal", is_open=False, centered=True,
            backdrop="static"),

        # Delete confirmation
        confirm_delete_modal("comments-comment", "comment"),
    ])


# ── Callbacks ───────────────────────────────────────────────────────


@callback(
    Output("comments-task-selector", "options"),
    Input("comments-refresh-interval", "n_intervals"),
)
def populate_task_selector(n):
    """Load tasks into the dropdown selector."""
    token = get_user_token()
    tasks = task_service.get_tasks(user_token=token)
    if tasks.empty:
        return []
    options = []
    for _, row in tasks.iterrows():
        task_id = row.get("task_id", "")
        title = row.get("title", "Untitled")
        status = row.get("status", "")
        label = f"{task_id} — {title} [{status}]"
        options.append({"label": label, "value": task_id})
    return options


@callback(
    Output("comments-kpi-strip", "children"),
    Output("comments-count-badge", "children"),
    Input("comments-task-selector", "value"),
    Input("comments-mutation-counter", "data"),
    Input("comments-refresh-interval", "n_intervals"),
)
def update_kpi_strip(task_id, mutation_count, n_intervals):
    """Update KPI cards based on selected task."""
    if not task_id:
        kpis = dbc.Row([
            dbc.Col(kpi_card("Total Comments", 0, "select a task", icon="chat-fill", icon_color="blue"), width=True),
            dbc.Col(kpi_card("Today's Comments", 0, "select a task", icon="calendar-event-fill", icon_color="purple"), width=True),
            dbc.Col(kpi_card("Active Discussions", 0, "tasks with comments", icon="chat-dots-fill", icon_color="green"), width=True),
            dbc.Col(kpi_card("Contributors", 0, "unique authors", icon="people-fill", icon_color="purple"), width=True),
        ], className="kpi-strip")
        return kpis, dbc.Badge("0", color="secondary", pill=True)

    token = get_user_token()
    comments = comment_service.get_comments(task_id, user_token=token)

    if comments.empty:
        total = 0
        today_count = 0
        contributors = 0
    else:
        # Filter for non-deleted if the sample data returns all
        if "is_deleted" in comments.columns:
            comments = comments[comments["is_deleted"] == False]  # noqa: E712
        # Filter for this task
        if "task_id" in comments.columns:
            comments = comments[comments["task_id"] == task_id]

        total = len(comments)

        # Today's comments
        today_str = str(date.today())
        today_count = 0
        if "created_at" in comments.columns:
            today_count = len(comments[
                comments["created_at"].astype(str).str.startswith(today_str)
            ])

        # Unique contributors
        contributors = 0
        if "author" in comments.columns:
            contributors = comments["author"].nunique()

    # Active discussions — count tasks that have comments across all tasks
    all_tasks_comments = comment_service.get_comments("__all__", user_token=token)
    active_discussions = 0
    if not all_tasks_comments.empty and "task_id" in all_tasks_comments.columns:
        if "is_deleted" in all_tasks_comments.columns:
            all_tasks_comments = all_tasks_comments[
                all_tasks_comments["is_deleted"] == False  # noqa: E712
            ]
        active_discussions = all_tasks_comments["task_id"].nunique()

    kpis = dbc.Row([
        dbc.Col(kpi_card("Total Comments", total, "on this task", icon="chat-fill", icon_color="blue"), width=True),
        dbc.Col(kpi_card("Today's Comments", today_count, str(date.today()), icon="calendar-event-fill", icon_color="purple"), width=True),
        dbc.Col(kpi_card("Active Discussions", active_discussions, "tasks with comments", icon="chat-dots-fill", icon_color="green"), width=True),
        dbc.Col(kpi_card("Contributors", contributors, "unique authors", icon="people-fill", icon_color="purple"), width=True),
    ], className="kpi-strip")

    badge = dbc.Badge(str(total), color="primary", pill=True)
    return kpis, badge


@callback(
    Output("comments-thread-area", "children"),
    Input("comments-task-selector", "value"),
    Input("comments-mutation-counter", "data"),
    Input("comments-refresh-interval", "n_intervals"),
)
def render_comment_thread(task_id, mutation_count, n_intervals):
    """Render the comment thread for the selected task."""
    if not task_id:
        return empty_state("Select a task to view comments.")

    token = get_user_token()
    email = get_user_email()
    comments = comment_service.get_comments(task_id, user_token=token)

    # Filter for this task in sample data mode (which returns all comments)
    if not comments.empty and "task_id" in comments.columns:
        comments = comments[comments["task_id"] == task_id]
    if not comments.empty and "is_deleted" in comments.columns:
        comments = comments[comments["is_deleted"] == False]  # noqa: E712
    # Sort by created_at ascending
    if not comments.empty and "created_at" in comments.columns:
        comments = comments.sort_values("created_at", ascending=True)

    comment_list = comment_list_display(comments, "comments", current_user=email)

    # Add comment form
    add_form = html.Div([
        html.Hr(className="my-3"),
        dbc.Label("Add a Comment", className="fw-bold small mb-1"),
        dbc.Textarea(
            id="comments-comment-input",
            placeholder="Write your comment here...",
            rows=3,
            className="mb-2",
        ),
        dbc.FormFeedback(
            id="comments-comment-input-feedback",
            type="invalid",
        ),
        html.Div([
            dbc.Button(
                [html.I(className="bi bi-chat-dots me-1"), "Post Comment"],
                id="comments-comment-submit",
                color="primary",
                size="sm",
            ),
        ], className="d-flex justify-content-end"),
    ])

    return html.Div([comment_list, add_form])


@callback(
    Output("comments-task-detail", "children"),
    Input("comments-task-selector", "value"),
)
def render_task_detail(task_id):
    """Show task details in the sidebar."""
    if not task_id:
        return empty_state("Select a task.")

    token = get_user_token()
    tasks = task_service.get_tasks(user_token=token)
    if tasks.empty:
        return empty_state("Task not found.")

    task_row = tasks[tasks["task_id"] == task_id]
    if task_row.empty:
        return empty_state("Task not found.")

    task = task_row.iloc[0]
    status = task.get("status", "unknown")
    status_colors = {
        "done": "success", "in_progress": "primary", "review": "info",
        "todo": "warning", "backlog": "secondary", "blocked": "danger",
    }

    return html.Div([
        html.H6(task.get("title", "Untitled"), className="fw-bold mb-3"),
        html.Div([
            html.Div([
                html.Small("Status", className="text-muted d-block"),
                dbc.Badge(
                    status.replace("_", " ").title(),
                    color=status_colors.get(status, "secondary"),
                ),
            ], className="mb-3"),
            html.Div([
                html.Small("Type", className="text-muted d-block"),
                html.Span(
                    (task.get("task_type") or "task").replace("_", " ").title(),
                    className="small",
                ),
            ], className="mb-3"),
            html.Div([
                html.Small("Assignee", className="text-muted d-block"),
                html.Span(
                    task.get("assignee_name") or "Unassigned",
                    className="small",
                ),
            ], className="mb-3"),
            html.Div([
                html.Small("Priority", className="text-muted d-block"),
                html.Span(
                    (task.get("priority") or "—").title(),
                    className="small",
                ),
            ], className="mb-3"),
            html.Div([
                html.Small("Story Points", className="text-muted d-block"),
                html.Span(
                    str(task.get("story_points") or "—"),
                    className="small",
                ),
            ], className="mb-3"),
            html.Div([
                html.Small("Sprint", className="text-muted d-block"),
                html.Span(
                    task.get("sprint_id") or "Unassigned",
                    className="small",
                ),
            ]),
        ]),
    ])


# ── Add Comment ──────────────────────────────────────────────────────


@callback(
    Output("comments-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input("comments-comment-submit", "n_clicks"),
    State("comments-task-selector", "value"),
    State("comments-comment-input", "value"),
    State("comments-mutation-counter", "data"),
    prevent_initial_call=True,
)
def add_comment(n_clicks, task_id, body, counter):
    """Create a new comment on the selected task."""
    if not task_id:
        return no_update, "Please select a task first", "Error", "danger", True
    if not body or not body.strip():
        return no_update, "Comment cannot be empty", "Error", "danger", True

    token = get_user_token()
    email = get_user_email()

    result = comment_service.create_comment_from_form(
        task_id, body, user_email=email, user_token=token,
    )
    if result["success"]:
        return (counter or 0) + 1, result["message"], "Success", "success", True
    return no_update, result["message"], "Error", "danger", True


# ── Edit Comment ─────────────────────────────────────────────────────


@callback(
    Output("comments-edit-modal", "is_open", allow_duplicate=True),
    Output("comments-edit-store", "data", allow_duplicate=True),
    Output("comments-edit-body", "value", allow_duplicate=True),
    Input({"type": "comments-comment-edit-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_edit_modal(n_clicks_list):
    """Open edit modal with comment data."""
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        return no_update, no_update, no_update

    # Check if any button was actually clicked
    if not any(n for n in n_clicks_list if n):
        return no_update, no_update, no_update

    comment_id = triggered["index"]
    token = get_user_token()
    comment_df = comment_service.get_comment(comment_id, user_token=token)

    if comment_df.empty:
        return no_update, no_update, no_update

    # In sample data mode, filter by comment_id
    if "comment_id" in comment_df.columns:
        row = comment_df[comment_df["comment_id"] == comment_id]
        if row.empty:
            return no_update, no_update, no_update
        comment = row.iloc[0]
    else:
        comment = comment_df.iloc[0]

    stored = {
        "comment_id": comment_id,
        "updated_at": str(comment.get("updated_at", "")),
    }
    return True, json.dumps(stored), comment.get("body", "")


@callback(
    Output("comments-edit-modal", "is_open", allow_duplicate=True),
    Output("comments-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input("comments-edit-save-btn", "n_clicks"),
    State("comments-edit-store", "data"),
    State("comments-edit-body", "value"),
    State("comments-mutation-counter", "data"),
    prevent_initial_call=True,
)
def save_edit_comment(n_clicks, stored_data, body, counter):
    """Save an edited comment."""
    if not stored_data:
        return no_update, no_update, no_update, no_update, no_update, no_update

    stored = json.loads(stored_data) if isinstance(stored_data, str) else stored_data
    comment_id = stored["comment_id"]
    expected = stored.get("updated_at", "")

    token = get_user_token()
    email = get_user_email()

    result = comment_service.update_comment_from_form(
        comment_id, body, expected,
        user_email=email, user_token=token,
    )
    if result["success"]:
        return False, (counter or 0) + 1, result["message"], "Success", "success", True
    return True, no_update, result["message"], "Error", "danger", True


@callback(
    Output("comments-edit-modal", "is_open", allow_duplicate=True),
    Input("comments-edit-cancel-btn", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_edit(n):
    """Close edit modal on cancel."""
    return False


# ── Delete Comment ───────────────────────────────────────────────────


@callback(
    Output("comments-comment-delete-modal", "is_open", allow_duplicate=True),
    Output("comments-comment-delete-target-store", "data", allow_duplicate=True),
    Input({"type": "comments-comment-delete-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_delete_modal(n_clicks_list):
    """Open delete confirmation with the comment ID."""
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        return no_update, no_update

    if not any(n for n in n_clicks_list if n):
        return no_update, no_update

    comment_id = triggered["index"]
    return True, comment_id


@callback(
    Output("comments-comment-delete-modal", "is_open", allow_duplicate=True),
    Output("comments-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input("comments-comment-delete-confirm-btn", "n_clicks"),
    State("comments-comment-delete-target-store", "data"),
    State("comments-mutation-counter", "data"),
    prevent_initial_call=True,
)
def confirm_delete_comment(n_clicks, comment_id, counter):
    """Soft-delete a comment."""
    if not comment_id:
        return no_update, no_update, no_update, no_update, no_update, no_update

    token = get_user_token()
    email = get_user_email()
    success = comment_service.delete_comment(comment_id, user_email=email,
                                              user_token=token)
    if success:
        return False, (counter or 0) + 1, "Comment deleted", "Deleted", "success", True
    return False, no_update, "Failed to delete comment", "Error", "danger", True
