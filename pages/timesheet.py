"""
Time Tracking Page — Log and manage time entries
==================================================
Time entry log table, CRUD modals, KPI cards, hours-by-task chart,
date range filter, project context via active-project-store.
"""

import json
from datetime import date, timedelta

import dash
from dash import html, dcc, callback, Input, Output, State, ctx, ALL, no_update
import dash_bootstrap_components as dbc
from services.auth_service import (
    get_user_token, get_user_email, get_current_user, has_permission,
)
from services import time_entry_service
from services.task_service import get_backlog as get_project_tasks
from components.kpi_card import kpi_card
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from components.crud_modal import (
    crud_modal, confirm_delete_modal, get_modal_values,
    set_field_errors, modal_field_states, modal_error_outputs,
)
from charts.theme import COLORS
from charts.timesheet_charts import hours_by_task_chart
from components.filter_bar import filter_bar

dash.register_page(__name__, path="/timesheet", name="Time Tracking")

# ── User mapping (for display) ───────────────────────────────────────

USER_OPTIONS = [
    {"label": "Cory S.", "value": "u-001"},
    {"label": "Chris J.", "value": "u-002"},
    {"label": "Anna K.", "value": "u-003"},
]

USER_NAMES = {u["value"]: u["label"] for u in USER_OPTIONS}


# ── CRUD Modal Field Definitions ─────────────────────────────────────

def _get_task_options(project_id=None):
    """Build task dropdown options from task service."""
    token = get_user_token()
    pid = project_id or "prj-001"
    tasks_df = get_project_tasks(project_id=pid, user_token=token)
    if tasks_df.empty:
        return []
    options = []
    for _, row in tasks_df.iterrows():
        task_id = row.get("task_id", "")
        title = row.get("title", "Untitled")
        options.append({"label": f"{task_id}: {title}", "value": task_id})
    return options


# Static field definitions — task options are populated dynamically
TIME_ENTRY_FIELDS = [
    {"id": "task_id", "label": "Task", "type": "select", "required": True,
     "options": []},
    {"id": "user_id", "label": "Team Member", "type": "select", "required": True,
     "options": USER_OPTIONS},
    {"id": "hours", "label": "Hours", "type": "number", "required": True,
     "min": 0.25, "max": 24, "placeholder": "e.g. 4.5"},
    {"id": "work_date", "label": "Work Date", "type": "date", "required": True},
    {"id": "notes", "label": "Notes", "type": "textarea", "required": False,
     "rows": 2, "placeholder": "What did you work on?"},
]


# ── Helper functions ─────────────────────────────────────────────────

def _build_content(project_id=None, date_start=None, date_end=None, sort_by=None):
    """Build the page content."""
    token = get_user_token()
    entries = time_entry_service.get_time_entries(
        project_id=project_id, user_token=token,
    )

    # Apply date range filter
    if not entries.empty and "work_date" in entries.columns:
        entries["work_date"] = entries["work_date"].astype(str)
        if date_start:
            entries = entries[entries["work_date"] >= str(date_start)]
        if date_end:
            entries = entries[entries["work_date"] <= str(date_end)]

    # Apply sort
    if not entries.empty and sort_by:
        if sort_by == "work_date" and "work_date" in entries.columns:
            entries = entries.sort_values("work_date", ascending=False)
        elif sort_by == "hours" and "hours" in entries.columns:
            entries = entries.sort_values("hours", ascending=False)
        elif sort_by == "task" and "task_title" in entries.columns:
            entries = entries.sort_values("task_title")

    # Compute KPIs
    if not entries.empty and "hours" in entries.columns:
        total_hours = entries["hours"].sum()
        # This week entries
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_entries = entries[entries["work_date"] >= str(week_start)]
        week_hours = week_entries["hours"].sum() if not week_entries.empty else 0.0
        # Unique work dates for avg
        unique_dates = entries["work_date"].nunique()
        avg_per_day = total_hours / unique_dates if unique_dates > 0 else 0.0
        # Unique contributors
        contributors = entries["user_id"].nunique() if "user_id" in entries.columns else 0
    else:
        total_hours = 0.0
        week_hours = 0.0
        avg_per_day = 0.0
        contributors = 0

    # Build chart
    chart_fig = hours_by_task_chart(entries)

    # Build table rows
    table_rows = []
    if not entries.empty:
        for _, row in entries.iterrows():
            eid = row.get("entry_id", "")
            user_id = row.get("user_id", "")
            user_name = USER_NAMES.get(user_id, user_id)

            table_rows.append(html.Tr([
                html.Td(
                    html.Small(row.get("task_title", row.get("task_id", "—"))),
                ),
                html.Td(html.Small(user_name)),
                html.Td(
                    html.Span(
                        f"{row.get('hours', 0):.1f}h",
                        style={"fontWeight": "bold"},
                    ),
                    className="text-center",
                ),
                html.Td(html.Small(str(row.get("work_date", "—")))),
                html.Td(
                    html.Small(
                        (row.get("notes") or "—")[:60],
                        className="text-muted",
                    ),
                ),
                html.Td([
                    dbc.Button(
                        html.I(className="bi bi-pencil-square"),
                        id={"type": "ts-entry-edit-btn", "index": eid},
                        size="sm", color="link", className="p-0 me-1 text-muted",
                    ),
                    dbc.Button(
                        html.I(className="bi bi-trash"),
                        id={"type": "ts-entry-delete-btn", "index": eid},
                        size="sm", color="link", className="p-0 text-muted",
                    ),
                ], className="d-flex align-items-center"),
            ]))

    return html.Div([
        html.Div([
            html.Div(html.I(className="bi bi-clock-history"), className="page-header-icon"),
            html.H4("Time Tracking", className="page-title"),
        ], className="page-header mb-3"),
        html.P(
            "Log time against tasks, track hours by team member, "
            "and review time allocation across the project.",
            className="page-subtitle mb-4",
        ),

        # KPI strip
        dbc.Row([
            dbc.Col(kpi_card("Total Hours", f"{total_hours:.1f}", "all time", icon="clock-fill", icon_color="blue"), width=True),
            dbc.Col(kpi_card("This Week", f"{week_hours:.1f}", "hours logged",
                             COLORS["green"] if week_hours > 0 else None, icon="calendar-week-fill", icon_color="green"), width=True),
            dbc.Col(kpi_card("Avg Hours/Day", f"{avg_per_day:.1f}", "per work day", icon="graph-up", icon_color="purple"), width=True),
            dbc.Col(kpi_card("Contributors", contributors, "team members",
                             COLORS["blue"] if contributors > 0 else None, icon="people-fill", icon_color="cyan"), width=True),
        ], className="kpi-strip mb-4"),

        # Chart + table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Hours by Task"),
                    dbc.CardBody(
                        dcc.Graph(
                            figure=chart_fig,
                            config={"displayModeBar": False},
                        ),
                    ),
                ], className="chart-card"),
            ], width=5),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Time Entry Log"),
                    dbc.CardBody([
                        dbc.Table([
                            html.Thead(html.Tr([
                                html.Th("Task", style={"width": "22%"}),
                                html.Th("Member"),
                                html.Th("Hours", className="text-center"),
                                html.Th("Date"),
                                html.Th("Notes"),
                                html.Th("Actions"),
                            ])),
                            html.Tbody(table_rows),
                        ], bordered=False, hover=True, responsive=True,
                            className="table-dark table-sm"),
                    ] if table_rows else [empty_state("No time entries found.")]),
                ], className="chart-card"),
            ], width=7),
        ]),
    ])


# ── Filter definitions ───────────────────────────────────────────────

TS_FILTERS = [
    {"id": "date-range", "label": "Date Range", "type": "date_range"},
]

TS_SORT_OPTIONS = [
    {"label": "Work Date", "value": "work_date"},
    {"label": "Hours", "value": "hours"},
    {"label": "Task", "value": "task"},
]


# ── Layout ───────────────────────────────────────────────────────────


def layout():
    user = get_current_user()
    can_write = has_permission(user, "create", "time_entry")
    return html.Div([
        # Stores
        dcc.Store(id="ts-mutation-counter", data=0),
        dcc.Store(id="ts-selected-entry-store", data=None),

        # Toolbar row
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    [html.I(className="bi bi-plus-circle me-1"), "Log Time"],
                    id="ts-add-entry-btn", color="primary", size="sm",
                    style={"display": "inline-block" if can_write else "none"},
                ),
            ], className="d-flex align-items-start justify-content-end"),
        ], className="mb-3"),

        # Filters
        filter_bar("ts", TS_FILTERS),

        # Sort
        html.Div([
            html.Small("Sort by", className="text-muted me-2",
                       style={"whiteSpace": "nowrap"}),
            dcc.Dropdown(
                id="ts-sort-toggle",
                options=TS_SORT_OPTIONS,
                value="work_date",
                clearable=False,
                style={"minWidth": "150px"},
                className="filter-dropdown",
            ),
        ], className="d-flex align-items-center mb-3"),

        # Content area
        html.Div(id="ts-content"),
        auto_refresh(interval_id="ts-refresh-interval"),

        # Modals
        crud_modal("ts-entry", "Log Time", TIME_ENTRY_FIELDS, size="lg"),
        confirm_delete_modal("ts-entry", "time entry"),
    ])


# ── Callbacks ────────────────────────────────────────────────────────


@callback(
    Output("ts-content", "children"),
    Input("ts-refresh-interval", "n_intervals"),
    Input("ts-mutation-counter", "data"),
    Input("active-project-store", "data"),
    Input("ts-date-range-filter", "start_date"),
    Input("ts-date-range-filter", "end_date"),
    Input("ts-sort-toggle", "value"),
)
def refresh_timesheet(n, mutation_count, active_project, date_start, date_end, sort_by):
    """Refresh time entry content on interval, mutation, or filter change."""
    return _build_content(
        project_id=active_project,
        date_start=date_start,
        date_end=date_end,
        sort_by=sort_by,
    )


@callback(
    Output("ts-entry-modal", "is_open", allow_duplicate=True),
    Output("ts-entry-modal-title", "children", allow_duplicate=True),
    Output("ts-selected-entry-store", "data", allow_duplicate=True),
    Output("ts-entry-task_id", "value", allow_duplicate=True),
    Output("ts-entry-task_id", "options", allow_duplicate=True),
    Output("ts-entry-user_id", "value", allow_duplicate=True),
    Output("ts-entry-hours", "value", allow_duplicate=True),
    Output("ts-entry-work_date", "value", allow_duplicate=True),
    Output("ts-entry-notes", "value", allow_duplicate=True),
    Input("ts-add-entry-btn", "n_clicks"),
    Input({"type": "ts-entry-edit-btn", "index": ALL}, "n_clicks"),
    State("active-project-store", "data"),
    prevent_initial_call=True,
)
def toggle_entry_modal(add_clicks, edit_clicks, active_project):
    """Open time entry modal for create (blank) or edit (populated)."""
    # Guard: ignore when fired by new components appearing (no actual click)
    triggered = ctx.triggered
    if not triggered or all(t.get("value") is None or t.get("value") == 0 for t in triggered):
        return (no_update,) * 9

    triggered_id = ctx.triggered_id

    # Build task options for the current project
    task_options = _get_task_options(project_id=active_project)

    # Create mode
    if triggered_id == "ts-add-entry-btn" and add_clicks:
        today_str = str(date.today())
        return (True, "Log Time", None,
                None, task_options, None, None, today_str, "")

    # Edit mode
    if isinstance(triggered_id, dict) and triggered_id.get("type") == "ts-entry-edit-btn":
        entry_id = triggered_id["index"]
        token = get_user_token()
        entry_df = time_entry_service.get_time_entry(entry_id, user_token=token)
        if entry_df.empty:
            return (no_update,) * 9
        entry = entry_df.iloc[0]
        stored = {"entry_id": entry_id, "updated_at": str(entry.get("updated_at", ""))}
        return (
            True, f"Edit Time Entry — {entry_id}", json.dumps(stored),
            entry.get("task_id"), task_options,
            entry.get("user_id"),
            entry.get("hours"),
            str(entry.get("work_date", "")),
            entry.get("notes", ""),
        )

    return (no_update,) * 9


@callback(
    Output("ts-entry-modal", "is_open", allow_duplicate=True),
    Output("ts-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    *modal_error_outputs("ts-entry", TIME_ENTRY_FIELDS),
    Input("ts-entry-save-btn", "n_clicks"),
    State("ts-selected-entry-store", "data"),
    State("ts-mutation-counter", "data"),
    *modal_field_states("ts-entry", TIME_ENTRY_FIELDS),
    prevent_initial_call=True,
)
def save_entry(n_clicks, stored_entry, counter, *field_values):
    """Save (create or update) a time entry."""
    if not n_clicks:
        return (no_update,) * (6 + len(TIME_ENTRY_FIELDS) * 2)
    form_data = get_modal_values("ts-entry", TIME_ENTRY_FIELDS, *field_values)

    token = get_user_token()
    email = get_user_email()

    if stored_entry:
        stored = json.loads(stored_entry) if isinstance(stored_entry, str) else stored_entry
        entry_id = stored["entry_id"]
        expected = stored.get("updated_at", "")
        result = time_entry_service.update_time_entry_from_form(
            entry_id, form_data, expected,
            user_email=email, user_token=token,
        )
    else:
        result = time_entry_service.create_time_entry_from_form(
            form_data, user_email=email, user_token=token,
        )

    if result["success"]:
        no_errors = set_field_errors("ts-entry", TIME_ENTRY_FIELDS, {})
        error_outputs = []
        for inv, fb in zip(no_errors[0], no_errors[1]):
            error_outputs.extend([inv, fb])
        return (False, (counter or 0) + 1, result["message"], "Success", "success", True,
                *error_outputs)

    errors = result.get("errors", {})
    field_errors = set_field_errors("ts-entry", TIME_ENTRY_FIELDS, errors)
    error_outputs = []
    for inv, fb in zip(field_errors[0], field_errors[1]):
        error_outputs.extend([inv, fb])
    return (True, no_update, result["message"], "Error", "danger", True,
            *error_outputs)


@callback(
    Output("ts-entry-delete-modal", "is_open", allow_duplicate=True),
    Output("ts-entry-delete-target-store", "data", allow_duplicate=True),
    Input({"type": "ts-entry-delete-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_delete_modal(n_clicks_list):
    """Open delete confirmation with the entry ID."""
    triggered = ctx.triggered
    if not triggered or all(t.get("value") is None or t.get("value") == 0 for t in triggered):
        return no_update, no_update
    triggered_id = ctx.triggered_id
    if not isinstance(triggered_id, dict):
        return no_update, no_update
    entry_id = triggered_id["index"]
    return True, entry_id


@callback(
    Output("ts-entry-delete-modal", "is_open", allow_duplicate=True),
    Output("ts-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input("ts-entry-delete-confirm-btn", "n_clicks"),
    State("ts-entry-delete-target-store", "data"),
    State("ts-mutation-counter", "data"),
    prevent_initial_call=True,
)
def confirm_delete_entry(n_clicks, entry_id, counter):
    """Soft-delete the time entry."""
    if not n_clicks:
        return (no_update,) * 6
    if not entry_id:
        return no_update, no_update, no_update, no_update, no_update, no_update

    token = get_user_token()
    email = get_user_email()
    success = time_entry_service.delete_time_entry(
        entry_id, user_email=email, user_token=token,
    )

    if success:
        return False, (counter or 0) + 1, "Time entry deleted", "Deleted", "success", True
    return False, no_update, "Failed to delete time entry", "Error", "danger", True


@callback(
    Output("ts-entry-modal", "is_open", allow_duplicate=True),
    Input("ts-entry-cancel-btn", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_entry_modal(n):
    """Close time entry modal on cancel."""
    return False
