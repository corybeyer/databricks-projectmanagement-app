"""
Gantt Timeline Page — Phase CRUD + Gate Approval
==================================================
Project phase Gantt chart with delivery method color coding,
full Phase CRUD (create/edit/delete), and Gate approval workflow.
"""

import json
import dash
from dash import html, dcc, callback, Input, Output, State, ctx, ALL, no_update
import dash_bootstrap_components as dbc
from services.auth_service import (
    get_user_token, get_user_email, get_current_user, has_permission,
)
from services.project_service import get_project_detail
from services import phase_service
from components.kpi_card import kpi_card
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from components.crud_modal import (
    crud_modal, confirm_delete_modal, get_modal_values,
    set_field_errors, modal_field_states, modal_error_outputs,
)
from charts.theme import COLORS
from charts.project_charts import gantt_chart

dash.register_page(__name__, path="/gantt", name="Gantt Timeline")

# ── Gate Status Colors ────────────────────────────────────────────────

GATE_STATUS_COLORS = {
    "pending": "warning",
    "approved": "success",
    "rejected": "danger",
    "deferred": "secondary",
}

# ── Phase CRUD Modal Field Definitions ────────────────────────────────

PHASE_FIELDS = [
    {"id": "name", "label": "Phase Name", "type": "text", "required": True,
     "placeholder": "e.g. Design, Build, UAT"},
    {"id": "phase_type", "label": "Phase Type", "type": "select", "required": True,
     "options": [{"label": t.title(), "value": t}
                 for t in sorted(["initiation", "planning", "design",
                                   "build", "test", "deploy", "closeout"])]},
    {"id": "delivery_method", "label": "Delivery Method", "type": "select", "required": True,
     "options": [{"label": m.title(), "value": m}
                 for m in ["waterfall", "agile"]]},
    {"id": "phase_order", "label": "Phase Order", "type": "number", "required": True,
     "min": 1, "max": 99, "placeholder": "Sequence number (1, 2, 3...)"},
    {"id": "start_date", "label": "Start Date", "type": "date", "required": False},
    {"id": "end_date", "label": "End Date", "type": "date", "required": False},
]

# ── Gate Create Modal Field Definitions ───────────────────────────────

GATE_FIELDS = [
    {"id": "name", "label": "Gate Name", "type": "text", "required": True,
     "placeholder": "e.g. Planning Gate, Build Gate"},
    {"id": "criteria", "label": "Gate Criteria", "type": "textarea", "required": False,
     "rows": 3, "placeholder": "What must be true for this gate to pass?"},
]


# ── Helper Functions ──────────────────────────────────────────────────


def _gate_status_badge(status):
    """Render a gate status badge."""
    color = GATE_STATUS_COLORS.get(status, "secondary")
    return dbc.Badge(
        status.replace("_", " ").title(),
        color=color,
        className="me-1",
    )


def _build_content(project_id=None):
    """Build the full page content: KPIs, gantt chart, phase table, gate table."""
    token = get_user_token()
    pid = project_id or "prj-001"
    phases = phase_service.get_phases(pid, user_token=token)
    gates = phase_service.get_gates(pid, user_token=token)
    project = get_project_detail(pid, user_token=token)

    project_name = project.iloc[0]["name"] if not project.empty else "Project"

    if not phases.empty:
        total_phases = len(phases)
        done_phases = len(phases[phases["status"].isin(["done", "complete"])])
        in_progress = len(phases[phases["status"].isin(["in_progress", "active"])])
    else:
        total_phases = done_phases = in_progress = 0

    # Gate KPIs
    if not gates.empty:
        total_gates = len(gates)
        approved_gates = len(gates[gates["status"] == "approved"])
        pending_gates = len(gates[gates["status"] == "pending"])
    else:
        total_gates = approved_gates = pending_gates = 0

    # Phase table rows with edit/delete buttons
    phase_rows = []
    if not phases.empty:
        for _, row in phases.iterrows():
            pid_val = row.get("phase_id", "")
            status = row.get("status", "not_started")
            if status in ("done", "complete"):
                status_color = "success"
            elif status in ("in_progress", "active"):
                status_color = "primary"
            else:
                status_color = "secondary"

            phase_rows.append(html.Tr([
                html.Td(row.get("name", ""), className="fw-bold"),
                html.Td(html.Small(
                    (row.get("phase_type") or "").replace("_", " ").title()
                )),
                html.Td(dbc.Badge(
                    (row.get("delivery_method") or "N/A").title(),
                    color="info",
                )),
                html.Td(dbc.Badge(
                    status.replace("_", " ").title(),
                    color=status_color,
                )),
                html.Td(
                    f"{row.get('done_count', 0)}/{row.get('task_count', 0)}",
                    className="text-center",
                ),
                html.Td(
                    dbc.Progress(
                        value=row.get("pct_complete", 0),
                        style={"height": "8px"},
                        color="success",
                    ),
                ),
                html.Td([
                    dbc.Button(
                        html.I(className="bi bi-pencil-square"),
                        id={"type": "gantt-phase-edit-btn", "index": pid_val},
                        size="sm", color="link", className="p-0 me-1 text-muted",
                    ),
                    dbc.Button(
                        html.I(className="bi bi-trash"),
                        id={"type": "gantt-phase-delete-btn", "index": pid_val},
                        size="sm", color="link", className="p-0 text-muted",
                    ),
                ], className="d-flex align-items-center"),
            ]))

    # Gate table rows with approve/reject/defer actions
    gate_rows = []
    if not gates.empty:
        for _, row in gates.iterrows():
            gid = row.get("gate_id", "")
            gstatus = row.get("status", "pending")
            criteria = row.get("criteria") or "No criteria defined"
            decision = row.get("decision") or ""
            decided_by = row.get("decided_by") or ""

            # Only show action buttons for pending gates
            if gstatus == "pending":
                actions = html.Td([
                    dbc.Button(
                        [html.I(className="bi bi-check-lg me-1"), "Approve"],
                        id={"type": "gantt-gate-approve-btn", "index": gid},
                        size="sm", color="success", outline=True,
                        className="me-1",
                    ),
                    dbc.Button(
                        [html.I(className="bi bi-x-lg me-1"), "Reject"],
                        id={"type": "gantt-gate-reject-btn", "index": gid},
                        size="sm", color="danger", outline=True,
                        className="me-1",
                    ),
                    dbc.Button(
                        "Defer",
                        id={"type": "gantt-gate-defer-btn", "index": gid},
                        size="sm", color="secondary", outline=True,
                    ),
                ])
            else:
                # Show decision info for decided gates
                actions = html.Td([
                    html.Small(decided_by, className="text-muted d-block"),
                    html.Small(
                        str(row.get("decided_at", ""))[:10],
                        className="text-muted",
                    ) if row.get("decided_at") else html.Span(),
                ])

            gate_rows.append(html.Tr([
                html.Td([
                    html.Div(row.get("name") or f"Gate {row.get('gate_order', '')}", className="fw-bold small"),
                    html.Small(
                        row.get("phase_name", ""),
                        className="text-muted",
                    ),
                ]),
                html.Td(_gate_status_badge(gstatus)),
                html.Td(html.Small(criteria[:80] + "..." if len(criteria) > 80 else criteria,
                                   className="text-muted")),
                html.Td(html.Small(decision[:60] + "..." if decision and len(decision) > 60 else decision or "",
                                   className="text-muted")),
                actions,
            ]))

    return html.Div([
        html.Div([
            html.Div(html.I(className="bi bi-bar-chart-steps"), className="page-header-icon"),
            html.H4("Gantt Timeline", className="page-title"),
        ], className="page-header mb-1"),
        html.P(project_name, className="page-subtitle mb-3",
               style={"color": COLORS["accent"]}),

        # Phase KPIs
        dbc.Row([
            dbc.Col(kpi_card("Total Phases", total_phases, "in project",
                             icon="layers-fill", icon_color="blue"), width=True),
            dbc.Col(kpi_card("Completed", done_phases,
                             f"{(done_phases / max(total_phases, 1) * 100):.0f}% done",
                             COLORS["green"],
                             icon="check-circle-fill", icon_color="green"), width=True),
            dbc.Col(kpi_card("In Progress", in_progress, "active now",
                             COLORS["accent"],
                             icon="play-circle-fill", icon_color="yellow"), width=True),
            dbc.Col(kpi_card("Gates Approved", f"{approved_gates}/{total_gates}",
                             "gate reviews",
                             COLORS["green"] if approved_gates == total_gates and total_gates > 0
                             else None,
                             icon="shield-check", icon_color="green"), width=True),
            dbc.Col(kpi_card("Gates Pending", pending_gates, "awaiting decision",
                             COLORS["yellow"] if pending_gates > 0 else None,
                             icon="hourglass-split", icon_color="orange"), width=True),
        ], className="kpi-strip mb-4"),

        # Gantt chart
        dbc.Card([
            dbc.CardHeader([
                html.Span("Phase Timeline", className="me-3"),
                html.Small([
                    html.Span("| ", style={"color": COLORS["purple"]}),
                    html.Span("Waterfall  ", className="text-muted me-2"),
                    html.Span("| ", style={"color": COLORS["yellow"]}),
                    html.Span("Agile  ", className="text-muted me-2"),
                    html.Span("| ", style={"color": COLORS["orange"]}),
                    html.Span("Hybrid", className="text-muted"),
                ]),
            ]),
            dbc.CardBody(
                dcc.Graph(
                    figure=gantt_chart(phases),
                    config={"displayModeBar": False},
                ) if not phases.empty else empty_state("No phase data available.")
            ),
        ], className="chart-card mb-4"),

        # Phase details table
        dbc.Card([
            dbc.CardHeader("Phase Details"),
            dbc.CardBody([
                dbc.Table([
                    html.Thead(html.Tr([
                        html.Th("Phase"),
                        html.Th("Type"),
                        html.Th("Method"),
                        html.Th("Status"),
                        html.Th("Tasks", className="text-center"),
                        html.Th("Progress"),
                        html.Th("Actions"),
                    ])),
                    html.Tbody(phase_rows),
                ], bordered=False, hover=True, responsive=True,
                    className="table-dark table-sm"),
            ] if phase_rows else [empty_state("No phase data.")]),
        ], className="mb-4"),

        # Gate review table
        dbc.Card([
            dbc.CardHeader("Gate Reviews"),
            dbc.CardBody([
                dbc.Table([
                    html.Thead(html.Tr([
                        html.Th("Gate"),
                        html.Th("Status"),
                        html.Th("Criteria"),
                        html.Th("Decision"),
                        html.Th("Actions"),
                    ])),
                    html.Tbody(gate_rows),
                ], bordered=False, hover=True, responsive=True,
                    className="table-dark table-sm"),
            ] if gate_rows else [empty_state("No gate data.")]),
        ]),
    ])


# ── Layout ──────────────────────────────────────────────────────────


def layout():
    user = get_current_user()
    can_write = has_permission(user, "create", "phase")
    return html.Div([
        # Stores
        dcc.Store(id="gantt-mutation-counter", data=0),
        dcc.Store(id="gantt-selected-phase-store", data=None),
        dcc.Store(id="gantt-gate-action-store", data=None),

        # Toolbar
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    [html.I(className="bi bi-plus-circle me-1"), "Add Phase"],
                    id="gantt-add-phase-btn", color="primary", size="sm",
                    className="me-2",
                    style={"display": "inline-block" if can_write else "none"},
                ),
                dbc.Button(
                    [html.I(className="bi bi-shield-check me-1"), "Add Gate"],
                    id="gantt-add-gate-btn", color="secondary", size="sm",
                    outline=True,
                    style={"display": "inline-block" if can_write else "none"},
                ),
            ], className="d-flex align-items-start justify-content-end"),
        ], className="mb-3"),

        # Content area
        html.Div(id="gantt-content"),
        auto_refresh(interval_id="gantt-refresh-interval"),

        # Phase CRUD modals
        crud_modal("gantt-phase", "Create Phase", PHASE_FIELDS),
        confirm_delete_modal("gantt-phase", "phase"),

        # Gate create modal
        crud_modal("gantt-gate", "Create Gate", GATE_FIELDS),

        # Gate decision modal (approve/reject/defer)
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Gate Decision", id="gantt-gate-decision-title")),
            dbc.ModalBody([
                dbc.Label("Decision Notes"),
                dbc.Textarea(
                    id="gantt-gate-decision-notes",
                    placeholder="Enter decision rationale...",
                    rows=3,
                ),
            ]),
            dbc.ModalFooter([
                dbc.Button(
                    "Cancel",
                    id="gantt-gate-decision-cancel-btn",
                    color="secondary", outline=True,
                ),
                dbc.Button(
                    "Confirm",
                    id="gantt-gate-decision-confirm-btn",
                    color="primary",
                ),
            ]),
        ], id="gantt-gate-decision-modal", is_open=False, centered=True,
           backdrop="static"),
    ])


# ── Callbacks ───────────────────────────────────────────────────────


@callback(
    Output("gantt-content", "children"),
    Input("gantt-refresh-interval", "n_intervals"),
    Input("gantt-mutation-counter", "data"),
    Input("active-project-store", "data"),
)
def refresh_gantt(n, mutation_count, active_project):
    """Refresh gantt content on interval, mutation, or project change."""
    return _build_content(project_id=active_project)


# ── Phase Modal: Open for Create or Edit ────────────────────────────


@callback(
    Output("gantt-phase-modal", "is_open", allow_duplicate=True),
    Output("gantt-phase-modal-title", "children", allow_duplicate=True),
    Output("gantt-selected-phase-store", "data", allow_duplicate=True),
    Output("gantt-phase-name", "value", allow_duplicate=True),
    Output("gantt-phase-phase_type", "value", allow_duplicate=True),
    Output("gantt-phase-delivery_method", "value", allow_duplicate=True),
    Output("gantt-phase-phase_order", "value", allow_duplicate=True),
    Output("gantt-phase-start_date", "value", allow_duplicate=True),
    Output("gantt-phase-end_date", "value", allow_duplicate=True),
    Input("gantt-add-phase-btn", "n_clicks"),
    Input({"type": "gantt-phase-edit-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def toggle_phase_modal(add_clicks, edit_clicks):
    """Open phase modal for create (blank) or edit (populated)."""
    # Guard: ignore when fired by new components appearing (no actual click)
    triggered = ctx.triggered
    if not triggered or all(t.get("value") is None or t.get("value") == 0 for t in triggered):
        return (no_update,) * 9

    triggered_id = ctx.triggered_id

    # Create mode
    if triggered_id == "gantt-add-phase-btn" and add_clicks:
        return (True, "Create Phase", None,
                "", None, None, None, None, None)

    # Edit mode
    if isinstance(triggered_id, dict) and triggered_id.get("type") == "gantt-phase-edit-btn":
        phase_id = triggered_id["index"]
        token = get_user_token()
        phase_df = phase_service.get_phase(phase_id, user_token=token)
        if phase_df.empty:
            return (no_update,) * 9
        phase = phase_df.iloc[0]
        stored = {"phase_id": phase_id, "updated_at": str(phase.get("updated_at", ""))}
        return (
            True, f"Edit Phase — {phase.get('name', phase_id)}", json.dumps(stored),
            phase.get("name", ""),
            phase.get("phase_type"),
            phase.get("delivery_method"),
            phase.get("phase_order"),
            str(phase.get("start_date", "")) if phase.get("start_date") else None,
            str(phase.get("end_date", "")) if phase.get("end_date") else None,
        )

    return (no_update,) * 9


# ── Phase Modal: Save (Create or Update) ────────────────────────────


@callback(
    Output("gantt-phase-modal", "is_open", allow_duplicate=True),
    Output("gantt-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    *modal_error_outputs("gantt-phase", PHASE_FIELDS),
    Input("gantt-phase-save-btn", "n_clicks"),
    State("gantt-selected-phase-store", "data"),
    State("gantt-mutation-counter", "data"),
    State("active-project-store", "data"),
    *modal_field_states("gantt-phase", PHASE_FIELDS),
    prevent_initial_call=True,
)
def save_phase(n_clicks, stored_phase, counter, active_project, *field_values):
    """Save (create or update) a phase."""
    if not n_clicks:
        return (no_update,) * (6 + len(PHASE_FIELDS) * 2)
    form_data = get_modal_values("gantt-phase", PHASE_FIELDS, *field_values)
    form_data["project_id"] = active_project or "prj-001"

    token = get_user_token()
    email = get_user_email()

    if stored_phase:
        stored = json.loads(stored_phase) if isinstance(stored_phase, str) else stored_phase
        phase_id = stored["phase_id"]
        expected = stored.get("updated_at", "")
        result = phase_service.update_phase_from_form(
            phase_id, form_data, expected,
            user_email=email, user_token=token,
        )
    else:
        result = phase_service.create_phase_from_form(
            form_data, user_email=email, user_token=token,
        )

    if result["success"]:
        no_errors = set_field_errors("gantt-phase", PHASE_FIELDS, {})
        error_outputs = []
        for inv, fb in zip(no_errors[0], no_errors[1]):
            error_outputs.extend([inv, fb])
        return (False, (counter or 0) + 1, result["message"], "Success", "success", True,
                *error_outputs)

    errors = result.get("errors", {})
    field_errors = set_field_errors("gantt-phase", PHASE_FIELDS, errors)
    error_outputs = []
    for inv, fb in zip(field_errors[0], field_errors[1]):
        error_outputs.extend([inv, fb])
    return (True, no_update, result["message"], "Error", "danger", True,
            *error_outputs)


# ── Phase Modal: Cancel ──────────────────────────────────────────────


@callback(
    Output("gantt-phase-modal", "is_open", allow_duplicate=True),
    Input("gantt-phase-cancel-btn", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_phase_modal(n):
    """Close phase modal on cancel."""
    return False


# ── Phase Delete: Open Confirm ───────────────────────────────────────


@callback(
    Output("gantt-phase-delete-modal", "is_open", allow_duplicate=True),
    Output("gantt-phase-delete-target-store", "data", allow_duplicate=True),
    Input({"type": "gantt-phase-delete-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_phase_delete_modal(n_clicks_list):
    """Open delete confirmation with the phase ID."""
    triggered = ctx.triggered
    if not triggered or all(t.get("value") is None or t.get("value") == 0 for t in triggered):
        return no_update, no_update
    triggered_id = ctx.triggered_id
    if not isinstance(triggered_id, dict):
        return no_update, no_update
    phase_id = triggered_id["index"]
    return True, phase_id


# ── Phase Delete: Confirm ────────────────────────────────────────────


@callback(
    Output("gantt-phase-delete-modal", "is_open", allow_duplicate=True),
    Output("gantt-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input("gantt-phase-delete-confirm-btn", "n_clicks"),
    State("gantt-phase-delete-target-store", "data"),
    State("gantt-mutation-counter", "data"),
    prevent_initial_call=True,
)
def confirm_delete_phase(n_clicks, phase_id, counter):
    """Soft-delete the phase."""
    if not n_clicks:
        return (no_update,) * 6
    if not phase_id:
        return no_update, no_update, no_update, no_update, no_update, no_update

    token = get_user_token()
    email = get_user_email()
    success = phase_service.delete_phase(phase_id, user_email=email, user_token=token)

    if success:
        return False, (counter or 0) + 1, "Phase deleted", "Deleted", "success", True
    return False, no_update, "Failed to delete phase", "Error", "danger", True


# ── Gate Create Modal: Open ──────────────────────────────────────────


@callback(
    Output("gantt-gate-modal", "is_open", allow_duplicate=True),
    Output("gantt-gate-modal-title", "children", allow_duplicate=True),
    Output("gantt-gate-name", "value", allow_duplicate=True),
    Output("gantt-gate-criteria", "value", allow_duplicate=True),
    Input("gantt-add-gate-btn", "n_clicks"),
    prevent_initial_call=True,
)
def open_gate_create_modal(n_clicks):
    """Open the gate create modal."""
    if not n_clicks:
        return (no_update,) * 4
    return True, "Create Gate", "", ""


# ── Gate Create Modal: Save ──────────────────────────────────────────


@callback(
    Output("gantt-gate-modal", "is_open", allow_duplicate=True),
    Output("gantt-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    *modal_error_outputs("gantt-gate", GATE_FIELDS),
    Input("gantt-gate-save-btn", "n_clicks"),
    State("gantt-mutation-counter", "data"),
    State("active-project-store", "data"),
    *modal_field_states("gantt-gate", GATE_FIELDS),
    prevent_initial_call=True,
)
def save_gate(n_clicks, counter, active_project, *field_values):
    """Create a new gate."""
    if not n_clicks:
        return (no_update,) * (6 + len(GATE_FIELDS) * 2)
    form_data = get_modal_values("gantt-gate", GATE_FIELDS, *field_values)

    # Determine the phase and gate order from existing data
    token = get_user_token()
    email = get_user_email()
    pid = active_project or "prj-001"
    phases = phase_service.get_phases(pid, user_token=token)
    gates = phase_service.get_gates(pid, user_token=token)

    # Assign gate to the last phase that doesn't have a gate yet, or the last phase
    if not phases.empty:
        existing_phase_ids = set(gates["phase_id"].tolist()) if not gates.empty else set()
        ungated = phases[~phases["phase_id"].isin(existing_phase_ids)]
        if not ungated.empty:
            target_phase_id = ungated.iloc[0]["phase_id"]
        else:
            target_phase_id = phases.iloc[-1]["phase_id"]
    else:
        target_phase_id = "ph-001"

    form_data["phase_id"] = target_phase_id
    form_data["gate_order"] = (len(gates) + 1) if not gates.empty else 1

    result = phase_service.create_gate_from_form(
        form_data, user_email=email, user_token=token,
    )

    if result["success"]:
        no_errors = set_field_errors("gantt-gate", GATE_FIELDS, {})
        error_outputs = []
        for inv, fb in zip(no_errors[0], no_errors[1]):
            error_outputs.extend([inv, fb])
        return (False, (counter or 0) + 1, result["message"], "Success", "success", True,
                *error_outputs)

    errors = result.get("errors", {})
    field_errors = set_field_errors("gantt-gate", GATE_FIELDS, errors)
    error_outputs = []
    for inv, fb in zip(field_errors[0], field_errors[1]):
        error_outputs.extend([inv, fb])
    return (True, no_update, result["message"], "Error", "danger", True,
            *error_outputs)


# ── Gate Create Modal: Cancel ────────────────────────────────────────


@callback(
    Output("gantt-gate-modal", "is_open", allow_duplicate=True),
    Input("gantt-gate-cancel-btn", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_gate_modal(n):
    """Close gate create modal on cancel."""
    return False


# ── Gate Decision: Open Modal ────────────────────────────────────────


@callback(
    Output("gantt-gate-decision-modal", "is_open", allow_duplicate=True),
    Output("gantt-gate-decision-title", "children", allow_duplicate=True),
    Output("gantt-gate-action-store", "data", allow_duplicate=True),
    Output("gantt-gate-decision-notes", "value", allow_duplicate=True),
    Input({"type": "gantt-gate-approve-btn", "index": ALL}, "n_clicks"),
    Input({"type": "gantt-gate-reject-btn", "index": ALL}, "n_clicks"),
    Input({"type": "gantt-gate-defer-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_gate_decision_modal(approve_clicks, reject_clicks, defer_clicks):
    """Open the gate decision modal for approve/reject/defer."""
    # Guard: ignore when fired by new components appearing (no actual click)
    triggered = ctx.triggered
    if not triggered or all(t.get("value") is None or t.get("value") == 0 for t in triggered):
        return (no_update,) * 4
    triggered_id = ctx.triggered_id
    if not isinstance(triggered_id, dict):
        return (no_update,) * 4

    gate_id = triggered_id["index"]
    action_type = triggered_id.get("type", "")

    if "approve" in action_type:
        action = "approve"
        title = f"Approve Gate — {gate_id}"
    elif "reject" in action_type:
        action = "reject"
        title = f"Reject Gate — {gate_id}"
    elif "defer" in action_type:
        action = "defer"
        title = f"Defer Gate — {gate_id}"
    else:
        return (no_update,) * 4

    stored = json.dumps({"gate_id": gate_id, "action": action})
    return True, title, stored, ""


# ── Gate Decision: Confirm ───────────────────────────────────────────


@callback(
    Output("gantt-gate-decision-modal", "is_open", allow_duplicate=True),
    Output("gantt-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input("gantt-gate-decision-confirm-btn", "n_clicks"),
    State("gantt-gate-action-store", "data"),
    State("gantt-gate-decision-notes", "value"),
    State("gantt-mutation-counter", "data"),
    prevent_initial_call=True,
)
def confirm_gate_decision(n_clicks, stored_action, decision_notes, counter):
    """Execute the gate decision (approve/reject/defer)."""
    if not n_clicks:
        return (no_update,) * 6
    if not stored_action:
        return (no_update,) * 6

    stored = json.loads(stored_action) if isinstance(stored_action, str) else stored_action
    gate_id = stored["gate_id"]
    action = stored["action"]

    token = get_user_token()
    email = get_user_email()
    notes = decision_notes or ""

    if action == "approve":
        result = phase_service.approve_gate(
            gate_id, notes, user_email=email, user_token=token,
        )
    elif action == "reject":
        result = phase_service.reject_gate(
            gate_id, notes, user_email=email, user_token=token,
        )
    elif action == "defer":
        result = phase_service.defer_gate(
            gate_id, notes, user_email=email, user_token=token,
        )
    else:
        return (no_update,) * 6

    if result["success"]:
        return False, (counter or 0) + 1, result["message"], "Gate Decision", "success", True
    return False, no_update, result["message"], "Error", "danger", True


# ── Gate Decision: Cancel ────────────────────────────────────────────


@callback(
    Output("gantt-gate-decision-modal", "is_open", allow_duplicate=True),
    Input("gantt-gate-decision-cancel-btn", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_gate_decision(n):
    """Close gate decision modal on cancel."""
    return False
