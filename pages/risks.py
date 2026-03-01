"""
Risk Register Page — PMI Risk Management (Full Lifecycle)
==========================================================
Risk heatmap (inherent + residual), risk table with inline status,
full CRUD modal with all PMI fields, delete confirmation, review action.
"""

import json
import dash
from dash import html, dcc, callback, Input, Output, State, ctx, ALL, no_update
import dash_bootstrap_components as dbc
from services.auth_service import (
    get_user_token, get_user_email, get_current_user, has_permission,
)
from services import risk_service
from services.analytics_service import get_risks_overdue_review
from components.kpi_card import kpi_card
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from components.crud_modal import (
    crud_modal, confirm_delete_modal, get_modal_values,
    set_field_errors, modal_field_states, modal_error_outputs,
)
from charts.theme import COLORS
from charts.analytics_charts import risk_heatmap, risk_heatmap_residual
from components.filter_bar import filter_bar, sort_toggle
from components.export_button import export_button

dash.register_page(__name__, path="/risks", name="Risk Register")

# ── PMI Risk Status Lifecycle ──────────────────────────────────────

RISK_STATUS_OPTIONS = [
    {"label": "Identified", "value": "identified"},
    {"label": "Qualitative Analysis", "value": "qualitative_analysis"},
    {"label": "Response Planning", "value": "response_planning"},
    {"label": "Monitoring", "value": "monitoring"},
    {"label": "Resolved", "value": "resolved"},
    {"label": "Closed", "value": "closed"},
]

RISK_STATUS_COLORS = {
    "identified": "info",
    "qualitative_analysis": "primary",
    "response_planning": "warning",
    "monitoring": "success",
    "resolved": "secondary",
    "closed": "dark",
}

# ── CRUD Modal Field Definitions ───────────────────────────────────

RISK_FIELDS = [
    {"id": "title", "label": "Risk Title", "type": "text", "required": True,
     "placeholder": "Brief risk description"},
    {"id": "category", "label": "Category", "type": "select", "required": True,
     "options": [{"label": c.replace("_", " ").title(), "value": c}
                 for c in sorted(["technical", "resource", "schedule", "scope",
                                   "budget", "external", "organizational"])]},
    {"id": "probability", "label": "Probability (1-5)", "type": "number",
     "required": True, "min": 1, "max": 5},
    {"id": "impact", "label": "Impact (1-5)", "type": "number",
     "required": True, "min": 1, "max": 5},
    {"id": "response_strategy", "label": "Response Strategy", "type": "select",
     "required": False,
     "options": [{"label": s.title(), "value": s}
                 for s in ["avoid", "transfer", "mitigate", "accept", "escalate"]]},
    {"id": "owner", "label": "Risk Owner", "type": "text", "required": False,
     "placeholder": "Who owns this risk?"},
    {"id": "response_owner", "label": "Response Owner", "type": "text",
     "required": False},
    {"id": "mitigation_plan", "label": "Mitigation Plan", "type": "textarea",
     "required": False, "rows": 2},
    {"id": "contingency_plan", "label": "Contingency Plan", "type": "textarea",
     "required": False, "rows": 2},
    {"id": "trigger_conditions", "label": "Trigger Conditions", "type": "textarea",
     "required": False, "rows": 2},
    {"id": "risk_proximity", "label": "Proximity", "type": "select",
     "required": False,
     "options": [{"label": "Near Term", "value": "near_term"},
                 {"label": "Mid Term", "value": "mid_term"},
                 {"label": "Long Term", "value": "long_term"}]},
    {"id": "risk_urgency", "label": "Urgency (1-5)", "type": "number",
     "required": False, "min": 1, "max": 5},
]


# ── Helper functions ───────────────────────────────────────────────


def _risk_status_badge(status):
    """Render a risk status badge with PMI lifecycle colors."""
    color = RISK_STATUS_COLORS.get(status, "secondary")
    return dbc.Badge(
        status.replace("_", " ").title(),
        color=color,
        className="me-1",
    )


def _risk_score_display(score):
    """Render a colored risk score."""
    if score is None:
        return html.Span("—", className="text-muted")
    score = int(score)
    if score >= 15:
        color = COLORS["red"]
    elif score >= 8:
        color = COLORS["yellow"]
    else:
        color = COLORS["green"]
    return html.Span(str(score), style={"color": color, "fontWeight": "bold"})


def _build_content(show_residual=False, status_filter=None, category_filter=None,
                   owner_search=None, sort_by=None):
    """Build the actual page content."""
    token = get_user_token()
    risks = risk_service.get_risks(user_token=token)

    # Apply filters
    if not risks.empty and status_filter:
        risks = risks[risks["status"].isin(status_filter)]
    if not risks.empty and category_filter and "category" in risks.columns:
        risks = risks[risks["category"].isin(category_filter)]
    if not risks.empty and owner_search and "owner" in risks.columns:
        risks = risks[risks["owner"].str.contains(owner_search, case=False, na=False)]

    # Apply sort
    if not risks.empty and sort_by:
        if sort_by == "risk_score":
            risks = risks.sort_values("risk_score", ascending=False)
        elif sort_by == "created_at" and "created_at" in risks.columns:
            risks = risks.sort_values("created_at", ascending=False)
        elif sort_by == "last_review_date" and "last_review_date" in risks.columns:
            risks = risks.sort_values("last_review_date", ascending=False)

    if not risks.empty:
        total = len(risks)
        high_risks = len(risks[risks["risk_score"] >= 15])
        avg_score = risks["risk_score"].mean()
        open_statuses = {"identified", "qualitative_analysis", "response_planning", "monitoring"}
        open_risks = len(risks[risks["status"].isin(open_statuses)])
    else:
        total = high_risks = open_risks = 0
        avg_score = 0.0

    # Overdue review count
    try:
        overdue = get_risks_overdue_review(user_token=token)
        overdue_count = len(overdue) if not overdue.empty else 0
    except Exception:
        overdue_count = 0

    # Decide which heatmap to show
    if show_residual and not risks.empty:
        has_residual = (
            "residual_probability" in risks.columns
            and "residual_impact" in risks.columns
            and risks["residual_probability"].notna().any()
        )
        if has_residual:
            heatmap_fig = risk_heatmap_residual(risks)
            heatmap_title = "Residual Risk Heatmap"
        else:
            heatmap_fig = risk_heatmap(risks)
            heatmap_title = "Inherent Risk Heatmap (no residual data)"
    elif not risks.empty:
        heatmap_fig = risk_heatmap(risks)
        heatmap_title = "Inherent Risk Heatmap"
    else:
        heatmap_fig = None
        heatmap_title = "Risk Heatmap"

    # Build risk table rows
    table_rows = []
    if not risks.empty:
        for _, row in risks.iterrows():
            rid = row.get("risk_id", "")
            res_score = row.get("residual_score")
            res_display = _risk_score_display(res_score) if res_score else html.Small("—", className="text-muted")
            proximity = row.get("risk_proximity", "")
            proximity_label = proximity.replace("_", " ").title() if proximity else "—"

            table_rows.append(html.Tr([
                html.Td([
                    html.Div(row.get("title", "Untitled"), className="fw-bold small"),
                    html.Small(
                        row.get("category", "").replace("_", " ").title(),
                        className="text-muted",
                    ),
                ]),
                html.Td(_risk_score_display(row.get("risk_score")), className="text-center"),
                html.Td(res_display, className="text-center"),
                html.Td(
                    dbc.Select(
                        id={"type": "risks-risk-status-dd", "index": rid},
                        options=RISK_STATUS_OPTIONS,
                        value=row.get("status", "identified"),
                        size="sm",
                    ),
                    style={"minWidth": "150px"},
                ),
                html.Td(
                    html.Small(
                        (row.get("response_strategy") or "—").replace("_", " ").title()
                    ),
                ),
                html.Td(html.Small(proximity_label)),
                html.Td(html.Small(row.get("owner") or "Unassigned")),
                html.Td([
                    dbc.Button(
                        html.I(className="bi bi-pencil-square"),
                        id={"type": "risks-risk-edit-btn", "index": rid},
                        size="sm", color="link", className="p-0 me-1 text-muted",
                    ),
                    dbc.Button(
                        html.I(className="bi bi-check-circle"),
                        id={"type": "risks-risk-review-btn", "index": rid},
                        size="sm", color="link", className="p-0 me-1 text-success",
                        title="Mark as reviewed",
                    ),
                    dbc.Button(
                        html.I(className="bi bi-trash"),
                        id={"type": "risks-risk-delete-btn", "index": rid},
                        size="sm", color="link", className="p-0 text-muted",
                    ),
                ], className="d-flex align-items-center"),
            ]))

    return html.Div([
        html.Div([
            html.Div(html.I(className="bi bi-shield-exclamation"), className="page-header-icon"),
            html.H4("Risk Register", className="page-title"),
        ], className="page-header mb-3"),
        html.P(
            "Track and manage project and portfolio risks with PMI lifecycle, "
            "probability/impact assessment, and mitigation planning.",
            className="page-subtitle mb-4",
        ),

        # KPI strip
        dbc.Row([
            dbc.Col(kpi_card("Total Risks", total, "registered", icon="shield-fill", icon_color="blue"), width=True),
            dbc.Col(kpi_card("High Severity", high_risks, "score >= 15",
                             COLORS["red"] if high_risks > 0 else None, icon="fire", icon_color="red"), width=True),
            dbc.Col(kpi_card("Avg Score", f"{avg_score:.1f}", "across all risks", icon="speedometer2", icon_color="yellow"), width=True),
            dbc.Col(kpi_card("Open / Active", open_risks, "need attention",
                             COLORS["yellow"] if open_risks > 0 else None, icon="exclamation-circle-fill", icon_color="orange"), width=True),
            dbc.Col(kpi_card("Overdue Review", overdue_count, "> 14 days",
                             COLORS["red"] if overdue_count > 0 else None, icon="clock-history", icon_color="red"), width=True),
        ], className="kpi-strip mb-4"),

        # Heatmap + table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(heatmap_title),
                    dbc.CardBody(
                        dcc.Graph(
                            figure=heatmap_fig,
                            config={"displayModeBar": False},
                        ) if heatmap_fig is not None else empty_state("No risk data.")
                    ),
                ], className="chart-card"),
            ], width=5),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Risk Details"),
                    dbc.CardBody([
                        dbc.Table([
                            html.Thead(html.Tr([
                                html.Th("Risk", style={"width": "22%"}),
                                html.Th("Score", className="text-center"),
                                html.Th("Resid.", className="text-center"),
                                html.Th("Status"),
                                html.Th("Strategy"),
                                html.Th("Proximity"),
                                html.Th("Owner"),
                                html.Th("Actions"),
                            ])),
                            html.Tbody(table_rows),
                        ], bordered=False, hover=True, responsive=True,
                            className="table-dark table-sm"),
                    ] if table_rows else [empty_state("No risks found.")]),
                ], className="chart-card"),
            ], width=7),
        ]),
    ])


# ── Layout ──────────────────────────────────────────────────────────


RISKS_FILTERS = [
    {"id": "status", "label": "Status", "type": "select", "multi": True,
     "options": RISK_STATUS_OPTIONS},
    {"id": "category", "label": "Category", "type": "select", "multi": True,
     "options": [{"label": c.replace("_", " ").title(), "value": c}
                 for c in sorted(["technical", "resource", "schedule", "scope",
                                   "budget", "external", "organizational"])]},
    {"id": "owner", "label": "Owner", "type": "text"},
]

RISKS_SORT_OPTIONS = [
    {"label": "Risk Score", "value": "risk_score"},
    {"label": "Created Date", "value": "created_at"},
    {"label": "Last Review", "value": "last_review_date"},
]


def layout():
    user = get_current_user()
    can_write = has_permission(user, "create", "risk")
    return html.Div([
        # Stores
        dcc.Store(id="risks-mutation-counter", data=0),
        dcc.Store(id="risks-selected-risk-store", data=None),
        dcc.Store(id="risks-show-residual-store", data=False),

        # Toolbar row
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    [html.I(className="bi bi-plus-circle me-1"), "Add Risk"],
                    id="risks-add-risk-btn", color="primary", size="sm",
                    className="me-2",
                    style={"display": "inline-block" if can_write else "none"},
                ),
                dbc.Button(
                    [html.I(className="bi bi-arrow-repeat me-1"), "Toggle Residual"],
                    id="risks-toggle-heatmap-btn", color="secondary", size="sm",
                    outline=True, className="me-2",
                ),
                export_button("risks-export-btn", "Export"),
            ], className="d-flex align-items-start justify-content-end"),
        ], className="mb-3"),

        # Filters
        filter_bar("risks", RISKS_FILTERS),
        sort_toggle("risks", RISKS_SORT_OPTIONS),

        # Content area
        html.Div(id="risks-content"),
        auto_refresh(interval_id="risks-refresh-interval"),

        # Modals
        crud_modal("risks-risk", "Create Risk", RISK_FIELDS, size="xl"),
        confirm_delete_modal("risks-risk", "risk"),
    ])


# ── Callbacks ───────────────────────────────────────────────────────


@callback(
    Output("risks-content", "children"),
    Input("risks-refresh-interval", "n_intervals"),
    Input("risks-mutation-counter", "data"),
    Input("risks-show-residual-store", "data"),
    Input("risks-status-filter", "value"),
    Input("risks-category-filter", "value"),
    Input("risks-owner-filter", "value"),
    Input("risks-sort-toggle", "value"),
)
def refresh_risks(n, mutation_count, show_residual, status_filter,
                  category_filter, owner_search, sort_by):
    """Refresh risk content on interval, mutation, or filter change."""
    return _build_content(
        show_residual=bool(show_residual),
        status_filter=status_filter,
        category_filter=category_filter,
        owner_search=owner_search,
        sort_by=sort_by,
    )


@callback(
    Output("risks-show-residual-store", "data"),
    Input("risks-toggle-heatmap-btn", "n_clicks"),
    State("risks-show-residual-store", "data"),
    prevent_initial_call=True,
)
def toggle_heatmap(n_clicks, current):
    """Switch between inherent and residual risk heatmap."""
    return not bool(current)


@callback(
    Output("risks-risk-modal", "is_open", allow_duplicate=True),
    Output("risks-risk-modal-title", "children", allow_duplicate=True),
    Output("risks-selected-risk-store", "data", allow_duplicate=True),
    Output("risks-risk-title", "value", allow_duplicate=True),
    Output("risks-risk-category", "value", allow_duplicate=True),
    Output("risks-risk-probability", "value", allow_duplicate=True),
    Output("risks-risk-impact", "value", allow_duplicate=True),
    Output("risks-risk-response_strategy", "value", allow_duplicate=True),
    Output("risks-risk-owner", "value", allow_duplicate=True),
    Output("risks-risk-response_owner", "value", allow_duplicate=True),
    Output("risks-risk-mitigation_plan", "value", allow_duplicate=True),
    Output("risks-risk-contingency_plan", "value", allow_duplicate=True),
    Output("risks-risk-trigger_conditions", "value", allow_duplicate=True),
    Output("risks-risk-risk_proximity", "value", allow_duplicate=True),
    Output("risks-risk-risk_urgency", "value", allow_duplicate=True),
    Input("risks-add-risk-btn", "n_clicks"),
    Input({"type": "risks-risk-edit-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def toggle_risk_modal(add_clicks, edit_clicks):
    """Open risk modal for create (blank) or edit (populated)."""
    # Guard: ignore when fired by new components appearing (no actual click)
    triggered = ctx.triggered
    if not triggered or all(t.get("value") is None or t.get("value") == 0 for t in triggered):
        return (no_update,) * 15

    triggered_id = ctx.triggered_id

    # Create mode
    if triggered_id == "risks-add-risk-btn" and add_clicks:
        return (True, "Create Risk", None,
                "", None, None, None, None, "", "", "", "", "", None, None)

    # Edit mode — pattern-match button
    if isinstance(triggered_id, dict) and triggered_id.get("type") == "risks-risk-edit-btn":
        risk_id = triggered_id["index"]
        token = get_user_token()
        risk_df = risk_service.get_risk(risk_id, user_token=token)
        if risk_df.empty:
            return (no_update,) * 15
        risk = risk_df.iloc[0]
        stored = {"risk_id": risk_id, "updated_at": str(risk.get("updated_at", ""))}
        return (
            True, f"Edit Risk — {risk_id}", json.dumps(stored),
            risk.get("title", ""),
            risk.get("category"),
            risk.get("probability"),
            risk.get("impact"),
            risk.get("response_strategy"),
            risk.get("owner", ""),
            risk.get("response_owner", ""),
            risk.get("mitigation_plan", ""),
            risk.get("contingency_plan", ""),
            risk.get("trigger_conditions", ""),
            risk.get("risk_proximity"),
            risk.get("risk_urgency"),
        )

    return (no_update,) * 15


@callback(
    Output("risks-risk-modal", "is_open", allow_duplicate=True),
    Output("risks-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    *modal_error_outputs("risks-risk", RISK_FIELDS),
    Input("risks-risk-save-btn", "n_clicks"),
    State("risks-selected-risk-store", "data"),
    State("risks-mutation-counter", "data"),
    *modal_field_states("risks-risk", RISK_FIELDS),
    prevent_initial_call=True,
)
def save_risk(n_clicks, stored_risk, counter, *field_values):
    """Save (create or update) a risk."""
    if not n_clicks:
        return (no_update,) * (6 + len(RISK_FIELDS) * 2)
    form_data = get_modal_values("risks-risk", RISK_FIELDS, *field_values)

    token = get_user_token()
    email = get_user_email()

    if stored_risk:
        stored = json.loads(stored_risk) if isinstance(stored_risk, str) else stored_risk
        risk_id = stored["risk_id"]
        expected = stored.get("updated_at", "")
        result = risk_service.update_risk_from_form(
            risk_id, form_data, expected,
            user_email=email, user_token=token,
        )
    else:
        result = risk_service.create_risk_from_form(
            form_data, user_email=email, user_token=token,
        )

    if result["success"]:
        no_errors = set_field_errors("risks-risk", RISK_FIELDS, {})
        error_outputs = []
        for inv, fb in zip(no_errors[0], no_errors[1]):
            error_outputs.extend([inv, fb])
        return (False, (counter or 0) + 1, result["message"], "Success", "success", True,
                *error_outputs)

    errors = result.get("errors", {})
    field_errors = set_field_errors("risks-risk", RISK_FIELDS, errors)
    error_outputs = []
    for inv, fb in zip(field_errors[0], field_errors[1]):
        error_outputs.extend([inv, fb])
    return (True, no_update, result["message"], "Error", "danger", True,
            *error_outputs)


@callback(
    Output("risks-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input({"type": "risks-risk-status-dd", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def change_risk_status(status_values):
    """Update risk status when inline dropdown changes."""
    triggered = ctx.triggered
    if not triggered or triggered[0]["value"] is None:
        return (no_update,) * 5

    prop_id = triggered[0]["prop_id"]
    try:
        id_dict = json.loads(prop_id.rsplit(".", 1)[0])
        risk_id = id_dict["index"]
    except (json.JSONDecodeError, KeyError):
        return (no_update,) * 5

    new_status = triggered[0]["value"]
    valid_statuses = {o["value"] for o in RISK_STATUS_OPTIONS}
    if new_status not in valid_statuses:
        return no_update, "Invalid status", "Error", "danger", True

    token = get_user_token()
    email = get_user_email()

    result = risk_service.update_risk_status(risk_id, new_status,
                                             user_email=email, user_token=token)
    if result["success"]:
        return 1, result["message"], "Status Updated", "success", True
    return no_update, result["message"], "Error", "danger", True


@callback(
    Output("risks-risk-delete-modal", "is_open", allow_duplicate=True),
    Output("risks-risk-delete-target-store", "data", allow_duplicate=True),
    Input({"type": "risks-risk-delete-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_delete_modal(n_clicks_list):
    """Open delete confirmation with the risk ID."""
    triggered = ctx.triggered
    if not triggered or all(t.get("value") is None or t.get("value") == 0 for t in triggered):
        return no_update, no_update
    triggered_id = ctx.triggered_id
    if not isinstance(triggered_id, dict):
        return no_update, no_update
    risk_id = triggered_id["index"]
    return True, risk_id


@callback(
    Output("risks-risk-delete-modal", "is_open", allow_duplicate=True),
    Output("risks-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input("risks-risk-delete-confirm-btn", "n_clicks"),
    State("risks-risk-delete-target-store", "data"),
    State("risks-mutation-counter", "data"),
    prevent_initial_call=True,
)
def confirm_delete_risk(n_clicks, risk_id, counter):
    """Soft-delete the risk."""
    if not n_clicks:
        return (no_update,) * 6
    if not risk_id:
        return no_update, no_update, no_update, no_update, no_update, no_update

    token = get_user_token()
    email = get_user_email()
    success = risk_service.delete_risk(risk_id, user_email=email, user_token=token)

    if success:
        return False, (counter or 0) + 1, "Risk deleted", "Deleted", "success", True
    return False, no_update, "Failed to delete risk", "Error", "danger", True


@callback(
    Output("risks-risk-modal", "is_open", allow_duplicate=True),
    Input("risks-risk-cancel-btn", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_risk_modal(n):
    """Close risk modal on cancel."""
    return False


@callback(
    Output("risks-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input({"type": "risks-risk-review-btn", "index": ALL}, "n_clicks"),
    State("risks-mutation-counter", "data"),
    prevent_initial_call=True,
)
def review_risk_action(n_clicks_list, counter):
    """Mark a risk as reviewed today."""
    triggered = ctx.triggered
    if not triggered or all(t.get("value") is None or t.get("value") == 0 for t in triggered):
        return (no_update,) * 5
    triggered_id = ctx.triggered_id
    if not isinstance(triggered_id, dict):
        return (no_update,) * 5

    risk_id = triggered_id["index"]
    token = get_user_token()
    email = get_user_email()

    result = risk_service.review_risk(risk_id, user_email=email, user_token=token)
    if result["success"]:
        return (counter or 0) + 1, result["message"], "Reviewed", "success", True
    return no_update, result["message"], "Error", "danger", True


@callback(
    Output("risks-export-btn-download", "data"),
    Input("risks-export-btn", "n_clicks"),
    prevent_initial_call=True,
)
def export_risks(n_clicks):
    """Export risk data to Excel."""
    if not n_clicks:
        return no_update
    from datetime import datetime
    from services import export_service
    token = get_user_token()
    df = risk_service.get_risks(user_token=token)
    excel_bytes = export_service.to_excel(df, "risks")
    return dcc.send_bytes(excel_bytes, f"risks_{datetime.now().strftime('%Y%m%d')}.xlsx")
