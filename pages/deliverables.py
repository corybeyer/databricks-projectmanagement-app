"""
Deliverables Tracking Page — Phase 4.2 PMI Deliverable Management
===================================================================
Deliverable table with status badges, owner, due dates, artifact links,
KPI cards, phase filter, project selector, full CRUD with inline status.
"""

import json
from datetime import date

import dash
from dash import html, dcc, callback, Input, Output, State, ctx, ALL, no_update
import dash_bootstrap_components as dbc
from services.auth_service import get_user_token, get_user_email
from services import deliverable_service, project_service
from components.kpi_card import kpi_card
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from components.crud_modal import (
    crud_modal, confirm_delete_modal, get_modal_values,
    set_field_errors, modal_field_states, modal_error_outputs,
)
from charts.theme import COLORS

dash.register_page(__name__, path="/deliverables", name="Deliverables")

# -- Deliverable Status Options -------------------------------------------

DELIVERABLE_STATUS_OPTIONS = [
    {"label": "Not Started", "value": "not_started"},
    {"label": "In Progress", "value": "in_progress"},
    {"label": "Complete", "value": "complete"},
    {"label": "Approved", "value": "approved"},
]

DELIVERABLE_STATUS_COLORS = {
    "not_started": "secondary",
    "in_progress": "primary",
    "complete": "success",
    "approved": "info",
}

# -- CRUD Modal Field Definitions -----------------------------------------

DELIVERABLE_FIELDS = [
    {"id": "name", "label": "Deliverable Name", "type": "text", "required": True,
     "placeholder": "Name of the deliverable"},
    {"id": "description", "label": "Description", "type": "textarea", "required": False,
     "rows": 3, "placeholder": "What is this deliverable?"},
    {"id": "status", "label": "Status", "type": "select", "required": False,
     "options": DELIVERABLE_STATUS_OPTIONS},
    {"id": "owner", "label": "Owner", "type": "text", "required": False,
     "placeholder": "Who owns this deliverable?"},
    {"id": "due_date", "label": "Due Date", "type": "date", "required": False},
    {"id": "artifact_url", "label": "Artifact URL", "type": "text", "required": False,
     "placeholder": "Link to the deliverable artifact"},
]


# -- Helpers ---------------------------------------------------------------


def _status_badge(status):
    """Render a deliverable status badge."""
    color = DELIVERABLE_STATUS_COLORS.get(status, "secondary")
    return dbc.Badge(
        status.replace("_", " ").title(),
        color=color,
        className="me-1",
    )


def _due_date_display(due_date_val, status):
    """Render due date with overdue highlighting."""
    if not due_date_val:
        return html.Small("No date", className="text-muted")
    try:
        if isinstance(due_date_val, str):
            due = date.fromisoformat(due_date_val)
        else:
            due = due_date_val
    except (ValueError, TypeError):
        return html.Small(str(due_date_val), className="text-muted")

    is_overdue = (
        due < date.today()
        and status not in ("complete", "approved")
    )
    style = {"color": COLORS["red"], "fontWeight": "bold"} if is_overdue else {}
    text = due.strftime("%b %d, %Y")
    if is_overdue:
        text += " (overdue)"
    return html.Small(text, style=style)


def _build_content(project_id=None, phase_filter=None, status_filter=None,
                   owner_search=None, sort_by=None):
    """Build the main deliverables content."""
    token = get_user_token()

    # Get deliverables
    if project_id:
        deliverables = deliverable_service.get_deliverables_by_project(
            project_id, user_token=token,
        )
    else:
        deliverables = deliverable_service.get_deliverables(user_token=token)

    # Apply phase filter
    if not deliverables.empty and phase_filter:
        if "phase_id" in deliverables.columns:
            deliverables = deliverables[
                deliverables["phase_id"].isin(phase_filter)
            ]

    # Apply status filter
    if not deliverables.empty and status_filter:
        deliverables = deliverables[
            deliverables["status"].isin(status_filter)
        ]

    # Apply owner search
    if not deliverables.empty and owner_search and "owner" in deliverables.columns:
        deliverables = deliverables[
            deliverables["owner"].str.contains(owner_search, case=False, na=False)
        ]

    # Apply sort
    if not deliverables.empty and sort_by:
        if sort_by == "due_date" and "due_date" in deliverables.columns:
            deliverables = deliverables.sort_values("due_date", ascending=True, na_position="last")
        elif sort_by == "status":
            status_order = {"not_started": 0, "in_progress": 1, "complete": 2, "approved": 3}
            deliverables = deliverables.copy()
            deliverables["_sort"] = deliverables["status"].map(status_order).fillna(99)
            deliverables = deliverables.sort_values("_sort").drop(columns=["_sort"])
        elif sort_by == "phase" and "phase_name" in deliverables.columns:
            deliverables = deliverables.sort_values("phase_name", ascending=True)

    # KPI calculations
    if not deliverables.empty:
        total = len(deliverables)
        in_progress = len(deliverables[deliverables["status"] == "in_progress"])
        completed = len(deliverables[deliverables["status"].isin({"complete", "approved"})])

        # Count overdue
        overdue_count = 0
        if "due_date" in deliverables.columns:
            for _, row in deliverables.iterrows():
                dd = row.get("due_date")
                st = row.get("status", "")
                if dd and st not in ("complete", "approved"):
                    try:
                        if isinstance(dd, str):
                            due = date.fromisoformat(dd)
                        else:
                            due = dd
                        if due < date.today():
                            overdue_count += 1
                    except (ValueError, TypeError):
                        pass
    else:
        total = in_progress = completed = overdue_count = 0

    # Build table rows
    table_rows = []
    if not deliverables.empty:
        for _, row in deliverables.iterrows():
            did = row.get("deliverable_id", "")
            phase_name = row.get("phase_name", "—")
            artifact_url = row.get("artifact_url")

            # Artifact link cell
            if artifact_url:
                artifact_cell = html.A(
                    html.I(className="bi bi-link-45deg"),
                    href=artifact_url, target="_blank",
                    className="text-info",
                    title=artifact_url,
                )
            else:
                artifact_cell = html.Small("—", className="text-muted")

            table_rows.append(html.Tr([
                html.Td([
                    html.Div(row.get("name", "Untitled"), className="fw-bold small"),
                    html.Small(phase_name, className="text-muted"),
                ]),
                html.Td(
                    dbc.Select(
                        id={"type": "deliv-status-dd", "index": did},
                        options=DELIVERABLE_STATUS_OPTIONS,
                        value=row.get("status", "not_started"),
                        size="sm",
                    ),
                    style={"minWidth": "140px"},
                ),
                html.Td(html.Small(row.get("owner") or "Unassigned")),
                html.Td(_due_date_display(
                    row.get("due_date"), row.get("status", ""),
                )),
                html.Td(artifact_cell, className="text-center"),
                html.Td([
                    dbc.Button(
                        html.I(className="bi bi-pencil-square"),
                        id={"type": "deliv-edit-btn", "index": did},
                        size="sm", color="link", className="p-0 me-1 text-muted",
                    ),
                    dbc.Button(
                        html.I(className="bi bi-trash"),
                        id={"type": "deliv-delete-btn", "index": did},
                        size="sm", color="link", className="p-0 text-muted",
                    ),
                ], className="d-flex align-items-center"),
            ]))

    return html.Div([
        html.H4("Deliverables", className="page-title mb-3"),
        html.P(
            "Track project deliverables across phases with status, ownership, "
            "due dates, and artifact links.",
            className="page-subtitle mb-4",
        ),

        # KPI strip
        dbc.Row([
            dbc.Col(kpi_card("Total", total, "deliverables"), width=True),
            dbc.Col(kpi_card("In Progress", in_progress, "active work",
                             COLORS.get("blue") if in_progress > 0 else None), width=True),
            dbc.Col(kpi_card("Completed", completed, "complete + approved",
                             COLORS["green"] if completed > 0 else None), width=True),
            dbc.Col(kpi_card("Overdue", overdue_count, "past due date",
                             COLORS["red"] if overdue_count > 0 else None), width=True),
        ], className="kpi-strip mb-4"),

        # Deliverables table
        dbc.Card([
            dbc.CardHeader("Deliverable Details"),
            dbc.CardBody([
                dbc.Table([
                    html.Thead(html.Tr([
                        html.Th("Deliverable", style={"width": "28%"}),
                        html.Th("Status"),
                        html.Th("Owner"),
                        html.Th("Due Date"),
                        html.Th("Artifact", className="text-center"),
                        html.Th("Actions"),
                    ])),
                    html.Tbody(table_rows),
                ], bordered=False, hover=True, responsive=True,
                    className="table-dark table-sm"),
            ] if table_rows else [empty_state("No deliverables found.")]),
        ], className="chart-card"),
    ])


# -- Layout ----------------------------------------------------------------


def layout():
    return html.Div([
        # Stores
        dcc.Store(id="deliv-mutation-counter", data=0),
        dcc.Store(id="deliv-selected-store", data=None),

        # Toolbar
        dbc.Row([
            dbc.Col([
                # Phase filter dropdown (populated dynamically)
                html.Div([
                    html.Small("Phase", className="text-muted d-block mb-1"),
                    dcc.Dropdown(
                        id="deliv-phase-filter",
                        multi=True,
                        placeholder="All Phases",
                        clearable=True,
                        className="filter-dropdown",
                    ),
                ], style={"minWidth": "200px"}),
            ], width=3),
            dbc.Col([
                html.Div([
                    html.Small("Status", className="text-muted d-block mb-1"),
                    dcc.Dropdown(
                        id="deliv-status-filter",
                        options=DELIVERABLE_STATUS_OPTIONS,
                        multi=True,
                        placeholder="All Statuses",
                        clearable=True,
                        className="filter-dropdown",
                    ),
                ]),
            ], width=2),
            dbc.Col([
                html.Div([
                    html.Small("Owner", className="text-muted d-block mb-1"),
                    dbc.Input(
                        id="deliv-owner-filter",
                        type="text",
                        placeholder="Search owner...",
                        size="sm",
                        debounce=True,
                    ),
                ]),
            ], width=2),
            dbc.Col([
                html.Div([
                    html.Small("Sort by", className="text-muted d-block mb-1"),
                    dcc.Dropdown(
                        id="deliv-sort-toggle",
                        options=[
                            {"label": "Due Date", "value": "due_date"},
                            {"label": "Status", "value": "status"},
                            {"label": "Phase", "value": "phase"},
                        ],
                        value="due_date",
                        clearable=False,
                        className="filter-dropdown",
                    ),
                ]),
            ], width=2),
            dbc.Col([
                html.Div([
                    html.Small("\u00a0", className="d-block mb-1"),
                    dbc.Button(
                        [html.I(className="bi bi-plus-circle me-1"), "Add Deliverable"],
                        id="deliv-add-btn", color="primary", size="sm",
                    ),
                ]),
            ], className="d-flex align-items-end justify-content-end", width=3),
        ], className="mb-3 align-items-end"),

        # Content area
        html.Div(id="deliv-content"),
        auto_refresh(interval_id="deliv-refresh-interval"),

        # Modals
        crud_modal("deliv-item", "Create Deliverable", DELIVERABLE_FIELDS, size="lg"),
        confirm_delete_modal("deliv-item", "deliverable"),
    ])


# -- Callbacks -------------------------------------------------------------

@callback(
    Output("deliv-phase-filter", "options"),
    Input("active-project-store", "data"),
)
def populate_phase_filter(active_project):
    """Populate phase filter dropdown from the active project's phases."""
    token = get_user_token()
    project_id = active_project if active_project else "prj-001"
    phases = project_service.get_project_phases(project_id, user_token=token)
    if phases.empty:
        return []
    options = []
    for _, ph in phases.iterrows():
        label = ph.get("name", ph.get("phase_id", ""))
        options.append({"label": label, "value": ph.get("phase_id", "")})
    return options


@callback(
    Output("deliv-content", "children"),
    Input("deliv-refresh-interval", "n_intervals"),
    Input("deliv-mutation-counter", "data"),
    Input("active-project-store", "data"),
    Input("deliv-phase-filter", "value"),
    Input("deliv-status-filter", "value"),
    Input("deliv-owner-filter", "value"),
    Input("deliv-sort-toggle", "value"),
)
def refresh_deliverables(n, mutation_count, active_project,
                         phase_filter, status_filter, owner_search, sort_by):
    """Refresh deliverable content on interval, mutation, or filter change."""
    project_id = active_project if active_project else None
    return _build_content(
        project_id=project_id,
        phase_filter=phase_filter,
        status_filter=status_filter,
        owner_search=owner_search,
        sort_by=sort_by,
    )


@callback(
    Output("deliv-item-modal", "is_open", allow_duplicate=True),
    Output("deliv-item-modal-title", "children", allow_duplicate=True),
    Output("deliv-selected-store", "data", allow_duplicate=True),
    Output("deliv-item-name", "value", allow_duplicate=True),
    Output("deliv-item-description", "value", allow_duplicate=True),
    Output("deliv-item-status", "value", allow_duplicate=True),
    Output("deliv-item-owner", "value", allow_duplicate=True),
    Output("deliv-item-due_date", "value", allow_duplicate=True),
    Output("deliv-item-artifact_url", "value", allow_duplicate=True),
    Input("deliv-add-btn", "n_clicks"),
    Input({"type": "deliv-edit-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def toggle_deliverable_modal(add_clicks, edit_clicks):
    """Open deliverable modal for create (blank) or edit (populated)."""
    triggered = ctx.triggered_id

    # Create mode
    if triggered == "deliv-add-btn":
        return (True, "Create Deliverable", None,
                "", "", "not_started", "", "", "")

    # Edit mode
    if isinstance(triggered, dict) and triggered.get("type") == "deliv-edit-btn":
        did = triggered["index"]
        token = get_user_token()
        df = deliverable_service.get_deliverable(did, user_token=token)
        if df.empty:
            return (no_update,) * 9
        row = df.iloc[0]
        stored = {
            "deliverable_id": did,
            "updated_at": str(row.get("updated_at", "")),
            "phase_id": str(row.get("phase_id", "")),
        }
        return (
            True, f"Edit Deliverable — {did}", json.dumps(stored),
            row.get("name", ""),
            row.get("description", "") or "",
            row.get("status", "not_started"),
            row.get("owner", "") or "",
            str(row.get("due_date", "")) if row.get("due_date") else "",
            row.get("artifact_url", "") or "",
        )

    return (no_update,) * 9


@callback(
    Output("deliv-item-modal", "is_open", allow_duplicate=True),
    Output("deliv-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    *modal_error_outputs("deliv-item", DELIVERABLE_FIELDS),
    Input("deliv-item-save-btn", "n_clicks"),
    State("deliv-selected-store", "data"),
    State("deliv-mutation-counter", "data"),
    State("active-project-store", "data"),
    State("deliv-phase-filter", "value"),
    *modal_field_states("deliv-item", DELIVERABLE_FIELDS),
    prevent_initial_call=True,
)
def save_deliverable(n_clicks, stored_item, counter, active_project,
                     phase_filter, *field_values):
    """Save (create or update) a deliverable."""
    form_data = get_modal_values("deliv-item", DELIVERABLE_FIELDS, *field_values)

    token = get_user_token()
    email = get_user_email()

    if stored_item:
        stored = json.loads(stored_item) if isinstance(stored_item, str) else stored_item
        did = stored["deliverable_id"]
        expected = stored.get("updated_at", "")
        form_data["phase_id"] = stored.get("phase_id", "ph-001")
        result = deliverable_service.update_deliverable_from_form(
            did, form_data, expected,
            user_email=email, user_token=token,
        )
    else:
        # For create, use first selected phase filter or default
        if phase_filter and isinstance(phase_filter, list) and len(phase_filter) > 0:
            form_data["phase_id"] = phase_filter[0]
        else:
            form_data["phase_id"] = "ph-001"
        result = deliverable_service.create_deliverable_from_form(
            form_data, user_email=email, user_token=token,
        )

    if result["success"]:
        no_errors = set_field_errors("deliv-item", DELIVERABLE_FIELDS, {})
        error_outputs = []
        for inv, fb in zip(no_errors[0], no_errors[1]):
            error_outputs.extend([inv, fb])
        return (False, (counter or 0) + 1, result["message"], "Success", "success", True,
                *error_outputs)

    errors = result.get("errors", {})
    field_errors = set_field_errors("deliv-item", DELIVERABLE_FIELDS, errors)
    error_outputs = []
    for inv, fb in zip(field_errors[0], field_errors[1]):
        error_outputs.extend([inv, fb])
    return (True, no_update, result["message"], "Error", "danger", True,
            *error_outputs)


@callback(
    Output("deliv-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input({"type": "deliv-status-dd", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def change_deliverable_status(status_values):
    """Update deliverable status when inline dropdown changes."""
    triggered = ctx.triggered
    if not triggered or triggered[0]["value"] is None:
        return (no_update,) * 5

    prop_id = triggered[0]["prop_id"]
    try:
        id_dict = json.loads(prop_id.rsplit(".", 1)[0])
        did = id_dict["index"]
    except (json.JSONDecodeError, KeyError):
        return (no_update,) * 5

    new_status = triggered[0]["value"]
    valid_statuses = {o["value"] for o in DELIVERABLE_STATUS_OPTIONS}
    if new_status not in valid_statuses:
        return no_update, "Invalid status", "Error", "danger", True

    token = get_user_token()
    email = get_user_email()

    result = deliverable_service.update_deliverable_status(
        did, new_status, user_email=email, user_token=token,
    )
    if result["success"]:
        return 1, result["message"], "Status Updated", "success", True
    return no_update, result["message"], "Error", "danger", True


@callback(
    Output("deliv-item-delete-modal", "is_open", allow_duplicate=True),
    Output("deliv-item-delete-target-store", "data", allow_duplicate=True),
    Input({"type": "deliv-delete-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_delete_modal(n_clicks_list):
    """Open delete confirmation with the deliverable ID."""
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        return no_update, no_update
    did = triggered["index"]
    return True, did


@callback(
    Output("deliv-item-delete-modal", "is_open", allow_duplicate=True),
    Output("deliv-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input("deliv-item-delete-confirm-btn", "n_clicks"),
    State("deliv-item-delete-target-store", "data"),
    State("deliv-mutation-counter", "data"),
    prevent_initial_call=True,
)
def confirm_delete_deliverable(n_clicks, did, counter):
    """Soft-delete the deliverable."""
    if not did:
        return no_update, no_update, no_update, no_update, no_update, no_update

    token = get_user_token()
    email = get_user_email()
    success = deliverable_service.delete_deliverable(
        did, user_email=email, user_token=token,
    )

    if success:
        return False, (counter or 0) + 1, "Deliverable deleted", "Deleted", "success", True
    return False, no_update, "Failed to delete deliverable", "Error", "danger", True


@callback(
    Output("deliv-item-modal", "is_open", allow_duplicate=True),
    Input("deliv-item-cancel-btn", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_deliverable_modal(n):
    """Close deliverable modal on cancel."""
    return False
