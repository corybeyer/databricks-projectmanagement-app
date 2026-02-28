"""
Project Charters Page
======================
Charter CRUD with approval workflow: draft -> submitted -> approved/rejected.
"""

import json
import pandas as pd
import dash
from dash import html, dcc, callback, Input, Output, State, ctx, ALL, no_update
import dash_bootstrap_components as dbc
from services.auth_service import get_user_token, get_user_email, get_current_user, has_permission
from services import charter_service
from components.charter_display import charter_display
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from components.crud_modal import (
    crud_modal, confirm_delete_modal, get_modal_values,
    set_field_errors, modal_field_states, modal_error_outputs,
)
from charts.theme import COLORS

dash.register_page(__name__, path="/charters", name="Project Charters")

STATUS_BADGE_COLORS = {
    "draft": "secondary",
    "submitted": "info",
    "under_review": "warning",
    "approved": "success",
    "rejected": "danger",
}

STATUS_LABELS = {
    "draft": "Draft",
    "submitted": "Submitted",
    "under_review": "Under Review",
    "approved": "Approved",
    "rejected": "Rejected",
}

CHARTER_FIELDS = [
    {"id": "project_name", "label": "Project Name", "type": "text", "required": True,
     "placeholder": "e.g., Unity Catalog Migration"},
    {"id": "delivery_method", "label": "Delivery Method", "type": "select", "required": True,
     "options": [
         {"label": "Waterfall", "value": "waterfall"},
         {"label": "Agile", "value": "agile"},
         {"label": "Hybrid", "value": "hybrid"},
     ]},
    {"id": "business_case", "label": "Business Case", "type": "textarea", "required": True,
     "rows": 3, "placeholder": "Why does this project exist? What problem does it solve?"},
    {"id": "objectives", "label": "Objectives", "type": "textarea", "required": True,
     "rows": 3, "placeholder": "1. Migrate 100% of tables by Q2\n2. Implement row-level security"},
    {"id": "scope_in", "label": "In Scope", "type": "textarea", "required": True,
     "rows": 3, "placeholder": "What IS included in this project"},
    {"id": "scope_out", "label": "Out of Scope", "type": "textarea", "required": False,
     "rows": 2, "placeholder": "What is explicitly NOT included"},
    {"id": "stakeholders", "label": "Stakeholders", "type": "textarea", "required": False,
     "rows": 2, "placeholder": "CIO (Sponsor), VP Data (Owner)"},
    {"id": "success_criteria", "label": "Success Criteria", "type": "textarea", "required": False,
     "rows": 2, "placeholder": "How do we know this project succeeded?"},
    {"id": "risks", "label": "Known Risks", "type": "textarea", "required": False,
     "rows": 2, "placeholder": "Resource contention, scope changes"},
    {"id": "budget", "label": "Budget", "type": "text", "required": False,
     "placeholder": "$420,000"},
    {"id": "timeline", "label": "Timeline", "type": "text", "required": False,
     "placeholder": "Jan 2026 — Aug 2026"},
    {"id": "description", "label": "Description", "type": "textarea", "required": False,
     "rows": 2, "placeholder": "Optional additional description"},
]


# ── Helper functions ────────────────────────────────────────────────


def _charter_card(charter_row):
    """Render a single charter as a card with action buttons."""
    c = charter_row
    charter_id = c.get("charter_id", "")
    status = c.get("status", "draft")
    badge_color = STATUS_BADGE_COLORS.get(status, "secondary")
    status_label = STATUS_LABELS.get(status, status.title())

    # Build action buttons based on current status
    action_buttons = []

    # Edit button — only for draft or rejected
    if status in ("draft", "rejected"):
        action_buttons.append(
            dbc.Button(
                [html.I(className="bi bi-pencil-square me-1"), "Edit"],
                id={"type": "charters-charter-edit-btn", "index": charter_id},
                size="sm", color="secondary", outline=True, className="me-1",
            )
        )

    # Submit button — only for draft or rejected
    if status in ("draft", "rejected"):
        action_buttons.append(
            dbc.Button(
                [html.I(className="bi bi-send me-1"), "Submit"],
                id={"type": "charters-charter-submit-btn", "index": charter_id},
                size="sm", color="info", outline=True, className="me-1",
            )
        )

    # Approve button — only for submitted or under_review
    if status in ("submitted", "under_review"):
        action_buttons.append(
            dbc.Button(
                [html.I(className="bi bi-check-circle me-1"), "Approve"],
                id={"type": "charters-charter-approve-btn", "index": charter_id},
                size="sm", color="success", outline=True, className="me-1",
            )
        )

    # Reject button — only for submitted or under_review
    if status in ("submitted", "under_review"):
        action_buttons.append(
            dbc.Button(
                [html.I(className="bi bi-x-circle me-1"), "Reject"],
                id={"type": "charters-charter-reject-btn", "index": charter_id},
                size="sm", color="danger", outline=True, className="me-1",
            )
        )

    # Delete button — always available
    action_buttons.append(
        dbc.Button(
            [html.I(className="bi bi-trash me-1"), "Delete"],
            id={"type": "charters-charter-delete-btn", "index": charter_id},
            size="sm", color="danger", outline=True,
        )
    )

    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.Div([
                    html.H5(
                        c.get("project_name", "Untitled Charter"),
                        className="mb-0 me-2",
                    ),
                    dbc.Badge(
                        status_label,
                        color=badge_color,
                        className="ms-2",
                    ),
                ], className="d-flex align-items-center"),
                html.Div(action_buttons, className="d-flex align-items-center"),
            ], className="d-flex justify-content-between align-items-center"),
        ]),
        dbc.CardBody([
            charter_display(
                # Pass the single row as a one-row DataFrame for charter_display
                pd.DataFrame([c])
            ),
        ]),
    ], className="mb-3")


def _build_content(project_id=None):
    """Build the charters page content."""
    token = get_user_token()
    pid = project_id or "prj-001"
    charters_df = charter_service.get_charters(pid, user_token=token)

    if charters_df.empty:
        return empty_state(
            "No charters found. Create a new charter to get started.",
        )

    # Filter out deleted charters
    if "is_deleted" in charters_df.columns:
        charters_df = charters_df[charters_df["is_deleted"] == False]  # noqa: E712

    if charters_df.empty:
        return empty_state(
            "No charters found. Create a new charter to get started.",
        )

    cards = []
    for _, row in charters_df.iterrows():
        cards.append(_charter_card(row.to_dict()))

    return html.Div(cards)


# ── Layout ──────────────────────────────────────────────────────────


def layout():
    user = get_current_user()
    can_write = has_permission(user, "create", "charter")
    return html.Div([
        # Stores
        dcc.Store(id="charters-mutation-counter", data=0),
        dcc.Store(id="charters-selected-charter-store", data=None),

        # Page header
        html.Div([
            html.Div(html.I(className="bi bi-file-earmark-text-fill"), className="page-header-icon"),
            html.H4("Project Charters", className="page-title"),
        ], className="page-header mb-1"),
        html.P(
            "Formal project authorization documents. Each charter defines the business case, "
            "scope, objectives, delivery method, and governance structure.",
            className="page-subtitle mb-3",
        ),

        # Toolbar
        dbc.Row([
            dbc.Col([], width=8),
            dbc.Col([
                dbc.Button(
                    [html.I(className="bi bi-plus-circle me-1"), "New Charter"],
                    id="charters-add-charter-btn", color="primary", size="sm",
                    style={"display": "inline-block" if can_write else "none"},
                ),
            ], width=4, className="d-flex align-items-start justify-content-end"),
        ], className="mb-3"),

        # Content area
        html.Div(id="charters-content"),
        auto_refresh(interval_id="charters-refresh-interval"),

        # Modals
        crud_modal("charters-charter", "Create Charter", CHARTER_FIELDS, size="xl"),
        confirm_delete_modal("charters-charter", "charter"),
    ])


# ── Callbacks ───────────────────────────────────────────────────────


@callback(
    Output("charters-content", "children"),
    Input("charters-refresh-interval", "n_intervals"),
    Input("charters-mutation-counter", "data"),
    Input("active-project-store", "data"),
)
def refresh_charters(n, mutation_count, active_project):
    """Refresh charters content on interval, mutation, or project change."""
    return _build_content(project_id=active_project)


@callback(
    Output("charters-charter-modal", "is_open", allow_duplicate=True),
    Output("charters-charter-modal-title", "children", allow_duplicate=True),
    Output("charters-selected-charter-store", "data", allow_duplicate=True),
    Output("charters-charter-project_name", "value", allow_duplicate=True),
    Output("charters-charter-delivery_method", "value", allow_duplicate=True),
    Output("charters-charter-business_case", "value", allow_duplicate=True),
    Output("charters-charter-objectives", "value", allow_duplicate=True),
    Output("charters-charter-scope_in", "value", allow_duplicate=True),
    Output("charters-charter-scope_out", "value", allow_duplicate=True),
    Output("charters-charter-stakeholders", "value", allow_duplicate=True),
    Output("charters-charter-success_criteria", "value", allow_duplicate=True),
    Output("charters-charter-risks", "value", allow_duplicate=True),
    Output("charters-charter-budget", "value", allow_duplicate=True),
    Output("charters-charter-timeline", "value", allow_duplicate=True),
    Output("charters-charter-description", "value", allow_duplicate=True),
    Input("charters-add-charter-btn", "n_clicks"),
    Input({"type": "charters-charter-edit-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def toggle_charter_modal(add_clicks, edit_clicks):
    """Open charter modal for create (blank) or edit (populated)."""
    triggered = ctx.triggered_id

    if triggered == "charters-add-charter-btn":
        return (True, "Create Charter", None,
                "", None, "", "", "", "", "", "", "", "", "", "")

    # Edit mode — pattern-match button
    if isinstance(triggered, dict) and triggered.get("type") == "charters-charter-edit-btn":
        charter_id = triggered["index"]
        token = get_user_token()
        charter_df = charter_service.get_charter(charter_id, user_token=token)
        if charter_df.empty:
            return (no_update,) * 15
        c = charter_df.iloc[0]
        stored = {"charter_id": charter_id, "updated_at": str(c.get("updated_at", ""))}
        return (
            True, f"Edit Charter — {c.get('project_name', charter_id)}",
            json.dumps(stored),
            c.get("project_name", ""),
            c.get("delivery_method"),
            c.get("business_case", ""),
            c.get("objectives", ""),
            c.get("scope_in", ""),
            c.get("scope_out", ""),
            c.get("stakeholders", ""),
            c.get("success_criteria", ""),
            c.get("risks", ""),
            c.get("budget", ""),
            c.get("timeline", ""),
            c.get("description", ""),
        )

    return (no_update,) * 15


@callback(
    Output("charters-charter-modal", "is_open", allow_duplicate=True),
    Output("charters-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    *modal_error_outputs("charters-charter", CHARTER_FIELDS),
    Input("charters-charter-save-btn", "n_clicks"),
    State("charters-selected-charter-store", "data"),
    State("charters-mutation-counter", "data"),
    State("active-project-store", "data"),
    *modal_field_states("charters-charter", CHARTER_FIELDS),
    prevent_initial_call=True,
)
def save_charter(n_clicks, stored_charter, counter, active_project, *field_values):
    """Save (create or update) a charter."""
    form_data = get_modal_values("charters-charter", CHARTER_FIELDS, *field_values)
    form_data["project_id"] = active_project or "prj-001"

    token = get_user_token()
    email = get_user_email()

    if stored_charter:
        stored = json.loads(stored_charter) if isinstance(stored_charter, str) else stored_charter
        charter_id = stored["charter_id"]
        expected = stored.get("updated_at", "")
        result = charter_service.update_charter_from_form(
            charter_id, form_data, expected,
            user_email=email, user_token=token,
        )
    else:
        result = charter_service.create_charter_from_form(
            form_data, user_email=email, user_token=token,
        )

    if result["success"]:
        no_errors = set_field_errors("charters-charter", CHARTER_FIELDS, {})
        error_outputs = []
        for inv, fb in zip(no_errors[0], no_errors[1]):
            error_outputs.extend([inv, fb])
        return (False, (counter or 0) + 1, result["message"], "Success", "success", True,
                *error_outputs)

    errors = result.get("errors", {})
    field_errors = set_field_errors("charters-charter", CHARTER_FIELDS, errors)
    error_outputs = []
    for inv, fb in zip(field_errors[0], field_errors[1]):
        error_outputs.extend([inv, fb])
    return (True, no_update, result["message"], "Error", "danger", True,
            *error_outputs)


@callback(
    Output("charters-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input({"type": "charters-charter-submit-btn", "index": ALL}, "n_clicks"),
    State("charters-mutation-counter", "data"),
    prevent_initial_call=True,
)
def submit_charter_action(n_clicks_list, counter):
    """Submit a charter for approval."""
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        return (no_update,) * 5

    charter_id = triggered["index"]
    token = get_user_token()
    email = get_user_email()
    result = charter_service.submit_charter(charter_id, user_email=email, user_token=token)

    if result["success"]:
        return (counter or 0) + 1, result["message"], "Submitted", "success", True
    return no_update, result["message"], "Error", "danger", True


@callback(
    Output("charters-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input({"type": "charters-charter-approve-btn", "index": ALL}, "n_clicks"),
    State("charters-mutation-counter", "data"),
    prevent_initial_call=True,
)
def approve_charter_action(n_clicks_list, counter):
    """Approve a submitted charter."""
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        return (no_update,) * 5

    charter_id = triggered["index"]
    token = get_user_token()
    email = get_user_email()
    result = charter_service.approve_charter(charter_id, user_email=email, user_token=token)

    if result["success"]:
        return (counter or 0) + 1, result["message"], "Approved", "success", True
    return no_update, result["message"], "Error", "danger", True


@callback(
    Output("charters-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input({"type": "charters-charter-reject-btn", "index": ALL}, "n_clicks"),
    State("charters-mutation-counter", "data"),
    prevent_initial_call=True,
)
def reject_charter_action(n_clicks_list, counter):
    """Reject a submitted charter."""
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        return (no_update,) * 5

    charter_id = triggered["index"]
    token = get_user_token()
    email = get_user_email()
    result = charter_service.reject_charter(charter_id, user_email=email, user_token=token)

    if result["success"]:
        return (counter or 0) + 1, result["message"], "Rejected", "warning", True
    return no_update, result["message"], "Error", "danger", True


@callback(
    Output("charters-charter-delete-modal", "is_open", allow_duplicate=True),
    Output("charters-charter-delete-target-store", "data", allow_duplicate=True),
    Input({"type": "charters-charter-delete-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_delete_modal(n_clicks_list):
    """Open delete confirmation with the charter ID."""
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        return no_update, no_update
    charter_id = triggered["index"]
    return True, charter_id


@callback(
    Output("charters-charter-delete-modal", "is_open", allow_duplicate=True),
    Output("charters-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input("charters-charter-delete-confirm-btn", "n_clicks"),
    State("charters-charter-delete-target-store", "data"),
    State("charters-mutation-counter", "data"),
    prevent_initial_call=True,
)
def confirm_delete_charter(n_clicks, charter_id, counter):
    """Soft-delete the charter."""
    if not charter_id:
        return no_update, no_update, no_update, no_update, no_update, no_update

    token = get_user_token()
    email = get_user_email()
    success = charter_service.delete_charter(charter_id, user_email=email, user_token=token)

    if success:
        return False, (counter or 0) + 1, "Charter deleted", "Deleted", "success", True
    return False, no_update, "Failed to delete charter", "Error", "danger", True


@callback(
    Output("charters-charter-modal", "is_open", allow_duplicate=True),
    Input("charters-charter-cancel-btn", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_charter_modal(n):
    """Close charter modal on cancel."""
    return False
