"""
Roadmap Timeline Page — with Dependency Management
====================================================
Cross-portfolio project timeline with health-coded bars and today marker.
Below the roadmap chart: full CRUD for cross-project dependencies with
KPI cards, risk-level color coding, inline status, and filter/sort controls.
"""

import json
import dash
from dash import html, dcc, callback, Input, Output, State, ctx, ALL, no_update
import dash_bootstrap_components as dbc
from services.auth_service import (
    get_user_token, get_user_email, get_current_user, has_permission,
)
from services.portfolio_service import get_portfolio_projects
from services import dependency_service
from components.kpi_card import kpi_card
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from components.crud_modal import (
    crud_modal, confirm_delete_modal, get_modal_values,
    set_field_errors, modal_field_states, modal_error_outputs,
)
from components.filter_bar import filter_bar, sort_toggle
from charts.portfolio_charts import roadmap_chart
from charts.theme import COLORS

dash.register_page(__name__, path="/roadmap", name="Roadmap Timeline")

# ── Dependency Constants ─────────────────────────────────────────────

DEP_TYPE_OPTIONS = [
    {"label": "Blocking", "value": "blocking"},
    {"label": "Dependent", "value": "dependent"},
    {"label": "Shared Resource", "value": "shared_resource"},
    {"label": "Informational", "value": "informational"},
]

DEP_RISK_OPTIONS = [
    {"label": "High", "value": "high"},
    {"label": "Medium", "value": "medium"},
    {"label": "Low", "value": "low"},
]

DEP_STATUS_OPTIONS = [
    {"label": "Active", "value": "active"},
    {"label": "Resolved", "value": "resolved"},
    {"label": "Accepted", "value": "accepted"},
]

DEP_TYPE_COLORS = {
    "blocking": COLORS["red"],
    "dependent": COLORS["orange"],
    "shared_resource": COLORS["yellow"],
    "informational": COLORS["blue"],
}

DEP_TYPE_ICONS = {
    "blocking": "bi bi-x-octagon-fill",
    "dependent": "bi bi-arrow-right-circle-fill",
    "shared_resource": "bi bi-people-fill",
    "informational": "bi bi-info-circle-fill",
}

DEP_RISK_COLORS = {
    "high": COLORS["red"],
    "medium": COLORS["yellow"],
    "low": COLORS["green"],
}

DEP_STATUS_BADGE_COLORS = {
    "active": "warning",
    "resolved": "success",
    "accepted": "info",
}

# ── Project options (for modal dropdowns) ────────────────────────────

PROJECT_OPTIONS = [
    {"label": "Unity Catalog Migration (prj-001)", "value": "prj-001"},
    {"label": "DLT Pipeline Framework (prj-002)", "value": "prj-002"},
    {"label": "Secrets Management Rollout (prj-003)", "value": "prj-003"},
]

# ── CRUD Modal Field Definitions ─────────────────────────────────────

DEP_FIELDS = [
    {"id": "source_project_id", "label": "Source Project", "type": "select",
     "required": True, "options": PROJECT_OPTIONS},
    {"id": "target_project_id", "label": "Target Project", "type": "select",
     "required": True, "options": PROJECT_OPTIONS},
    {"id": "dependency_type", "label": "Dependency Type", "type": "select",
     "required": True, "options": DEP_TYPE_OPTIONS},
    {"id": "risk_level", "label": "Risk Level", "type": "select",
     "required": True, "options": DEP_RISK_OPTIONS},
    {"id": "status", "label": "Status", "type": "select",
     "required": False, "options": DEP_STATUS_OPTIONS},
    {"id": "description", "label": "Description", "type": "textarea",
     "required": False, "rows": 3, "placeholder": "Describe the dependency..."},
]


# ── Helper functions ─────────────────────────────────────────────────


def _dep_type_badge(dep_type):
    """Render a dependency type badge with icon and color."""
    color = DEP_TYPE_COLORS.get(dep_type, COLORS["text_muted"])
    icon_cls = DEP_TYPE_ICONS.get(dep_type, "bi bi-link-45deg")
    label = (dep_type or "unknown").replace("_", " ").title()
    return html.Span([
        html.I(className=f"{icon_cls} me-1"),
        label,
    ], style={"color": color, "fontWeight": "600", "fontSize": "0.85rem"})


def _risk_level_badge(risk_level):
    """Render a risk level indicator with color coding."""
    color = DEP_RISK_COLORS.get(risk_level, COLORS["text_muted"])
    label = (risk_level or "unknown").title()
    return html.Span(label, style={
        "color": color, "fontWeight": "bold", "fontSize": "0.85rem",
    })


def _dep_status_badge(status):
    """Render a status badge."""
    color = DEP_STATUS_BADGE_COLORS.get(status, "secondary")
    return dbc.Badge(
        (status or "unknown").replace("_", " ").title(),
        color=color, className="me-1",
    )


def _build_content(type_filter=None, risk_filter=None, status_filter=None,
                   sort_by=None):
    """Build the full roadmap page content."""
    token = get_user_token()

    # ── Roadmap Chart ────────────────────────────────────────────
    projects = get_portfolio_projects("pf-001", user_token=token)

    roadmap_section = dbc.Card([
        dbc.CardHeader("Project Timeline"),
        dbc.CardBody(
            dcc.Graph(
                figure=roadmap_chart(projects),
                config={"displayModeBar": False},
                style={"height": "500px"},
            ) if not projects.empty else empty_state("No project data available.")
        ),
    ], className="chart-card mb-4")

    # ── Dependencies ─────────────────────────────────────────────
    deps = dependency_service.get_dependencies(user_token=token)

    # Apply filters
    if not deps.empty and type_filter:
        deps = deps[deps["dependency_type"].isin(type_filter)]
    if not deps.empty and risk_filter:
        deps = deps[deps["risk_level"].isin(risk_filter)]
    if not deps.empty and status_filter:
        deps = deps[deps["status"].isin(status_filter)]

    # Apply sort
    if not deps.empty and sort_by:
        if sort_by == "risk_level":
            risk_order = {"high": 0, "medium": 1, "low": 2}
            deps = deps.copy()
            deps["_sort_key"] = deps["risk_level"].map(risk_order).fillna(3)
            deps = deps.sort_values("_sort_key").drop(columns=["_sort_key"])
        elif sort_by == "dependency_type":
            deps = deps.sort_values("dependency_type")
        elif sort_by == "created_at" and "created_at" in deps.columns:
            deps = deps.sort_values("created_at", ascending=False)

    # KPI calculations
    if not deps.empty:
        total_deps = len(deps)
        high_risk = len(deps[deps["risk_level"] == "high"])
        active_blocking = len(
            deps[(deps["status"] == "active") & (deps["dependency_type"] == "blocking")]
        )
        resolved = len(deps[deps["status"] == "resolved"])
    else:
        total_deps = high_risk = active_blocking = resolved = 0

    # KPI strip
    kpi_strip = dbc.Row([
        dbc.Col(kpi_card("Total Dependencies", total_deps, "registered",
                         icon="diagram-3-fill", icon_color="blue"), width=True),
        dbc.Col(kpi_card("High Risk", high_risk, "dependencies",
                         COLORS["red"] if high_risk > 0 else None,
                         icon="exclamation-triangle-fill", icon_color="red"), width=True),
        dbc.Col(kpi_card("Active Blocking", active_blocking, "need attention",
                         COLORS["yellow"] if active_blocking > 0 else None,
                         icon="x-octagon-fill", icon_color="yellow"), width=True),
        dbc.Col(kpi_card("Resolved", resolved, "completed",
                         COLORS["green"] if resolved > 0 else None,
                         icon="check-circle-fill", icon_color="green"), width=True),
    ], className="kpi-strip mb-4")

    # Build dependency table rows
    table_rows = []
    if not deps.empty:
        for _, row in deps.iterrows():
            did = row.get("dependency_id", "")
            source_name = row.get("source_project_name", row.get("source_project_id", ""))
            target_name = row.get("target_project_name", row.get("target_project_id", ""))

            table_rows.append(html.Tr([
                html.Td([
                    html.Div(source_name, className="fw-bold small"),
                    html.Small(
                        row.get("source_task_id") or "",
                        className="text-muted",
                    ),
                ]),
                html.Td(
                    html.I(className="bi bi-arrow-right", style={"color": COLORS["text_muted"]}),
                    className="text-center",
                ),
                html.Td([
                    html.Div(target_name, className="fw-bold small"),
                    html.Small(
                        row.get("target_task_id") or "",
                        className="text-muted",
                    ),
                ]),
                html.Td(_dep_type_badge(row.get("dependency_type")), className="text-center"),
                html.Td(_risk_level_badge(row.get("risk_level")), className="text-center"),
                html.Td(
                    dbc.Select(
                        id={"type": "roadmap-dep-status-dd", "index": did},
                        options=DEP_STATUS_OPTIONS,
                        value=row.get("status", "active"),
                        size="sm",
                    ),
                    style={"minWidth": "120px"},
                ),
                html.Td(
                    html.Small(
                        (row.get("description") or "")[:60] + ("..." if len(row.get("description") or "") > 60 else ""),
                        className="text-muted",
                    ),
                ),
                html.Td([
                    dbc.Button(
                        html.I(className="bi bi-pencil-square"),
                        id={"type": "roadmap-dep-edit-btn", "index": did},
                        size="sm", color="link", className="p-0 me-1 text-muted",
                    ),
                    dbc.Button(
                        html.I(className="bi bi-check-circle"),
                        id={"type": "roadmap-dep-resolve-btn", "index": did},
                        size="sm", color="link", className="p-0 me-1 text-success",
                        title="Mark as resolved",
                    ),
                    dbc.Button(
                        html.I(className="bi bi-trash"),
                        id={"type": "roadmap-dep-delete-btn", "index": did},
                        size="sm", color="link", className="p-0 text-muted",
                    ),
                ], className="d-flex align-items-center"),
            ]))

    dep_table = dbc.Card([
        dbc.CardHeader("Cross-Project Dependencies"),
        dbc.CardBody([
            dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Source Project", style={"width": "16%"}),
                    html.Th("", style={"width": "3%"}),
                    html.Th("Target Project", style={"width": "16%"}),
                    html.Th("Type", className="text-center"),
                    html.Th("Risk", className="text-center"),
                    html.Th("Status"),
                    html.Th("Description"),
                    html.Th("Actions"),
                ])),
                html.Tbody(table_rows),
            ], bordered=False, hover=True, responsive=True,
                className="table-dark table-sm"),
        ] if table_rows else [empty_state("No dependencies found. Add one to track cross-project relationships.")]),
    ], className="chart-card")

    return html.Div([
        html.Div([
            html.Div(html.I(className="bi bi-calendar-range-fill"), className="page-header-icon"),
            html.H4("Roadmap Timeline", className="page-title"),
        ], className="page-header mb-3"),
        html.P(
            "Cross-portfolio project timeline and dependency management. "
            "Track blocking relationships, shared resources, and risk levels.",
            className="page-subtitle mb-4",
        ),
        roadmap_section,

        # Dependencies header
        html.H5("Dependencies", className="page-title mb-3 mt-2"),
        kpi_strip,
        dep_table,
    ])


# ── Filters & Sort ───────────────────────────────────────────────────

DEP_FILTERS = [
    {"id": "type", "label": "Type", "type": "select", "multi": True,
     "options": DEP_TYPE_OPTIONS},
    {"id": "risk", "label": "Risk Level", "type": "select", "multi": True,
     "options": DEP_RISK_OPTIONS},
    {"id": "status", "label": "Status", "type": "select", "multi": True,
     "options": DEP_STATUS_OPTIONS},
]

DEP_SORT_OPTIONS = [
    {"label": "Risk Level", "value": "risk_level"},
    {"label": "Type", "value": "dependency_type"},
    {"label": "Created Date", "value": "created_at"},
]


# ── Layout ───────────────────────────────────────────────────────────


def layout():
    user = get_current_user()
    can_write = has_permission(user, "create", "dependency")
    return html.Div([
        # Stores
        dcc.Store(id="roadmap-mutation-counter", data=0),
        dcc.Store(id="roadmap-selected-dep-store", data=None),

        # Toolbar row
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    [html.I(className="bi bi-plus-circle me-1"), "Add Dependency"],
                    id="roadmap-add-dep-btn", color="primary", size="sm",
                    className="me-2",
                    style={"display": "inline-block" if can_write else "none"},
                ),
            ], className="d-flex align-items-start justify-content-end"),
        ], className="mb-3"),

        # Filters
        filter_bar("roadmap", DEP_FILTERS),
        sort_toggle("roadmap", DEP_SORT_OPTIONS),

        # Content area
        html.Div(id="roadmap-content"),
        auto_refresh(interval_id="roadmap-refresh-interval"),

        # Modals
        crud_modal("roadmap-dep", "Create Dependency", DEP_FIELDS, size="lg"),
        confirm_delete_modal("roadmap-dep", "dependency"),
    ])


# ── Callbacks ────────────────────────────────────────────────────────


@callback(
    Output("roadmap-content", "children"),
    Input("roadmap-refresh-interval", "n_intervals"),
    Input("roadmap-mutation-counter", "data"),
    Input("roadmap-type-filter", "value"),
    Input("roadmap-risk-filter", "value"),
    Input("roadmap-status-filter", "value"),
    Input("roadmap-sort-toggle", "value"),
)
def refresh_roadmap(n, mutation_count, type_filter, risk_filter,
                    status_filter, sort_by):
    """Refresh roadmap content on interval, mutation, or filter change."""
    return _build_content(
        type_filter=type_filter,
        risk_filter=risk_filter,
        status_filter=status_filter,
        sort_by=sort_by,
    )


@callback(
    Output("roadmap-dep-modal", "is_open", allow_duplicate=True),
    Output("roadmap-dep-modal-title", "children", allow_duplicate=True),
    Output("roadmap-selected-dep-store", "data", allow_duplicate=True),
    Output("roadmap-dep-source_project_id", "value", allow_duplicate=True),
    Output("roadmap-dep-target_project_id", "value", allow_duplicate=True),
    Output("roadmap-dep-dependency_type", "value", allow_duplicate=True),
    Output("roadmap-dep-risk_level", "value", allow_duplicate=True),
    Output("roadmap-dep-status", "value", allow_duplicate=True),
    Output("roadmap-dep-description", "value", allow_duplicate=True),
    Input("roadmap-add-dep-btn", "n_clicks"),
    Input({"type": "roadmap-dep-edit-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def toggle_dep_modal(add_clicks, edit_clicks):
    """Open dependency modal for create (blank) or edit (populated)."""
    triggered = ctx.triggered_id

    # Create mode
    if triggered == "roadmap-add-dep-btn":
        return (True, "Create Dependency", None,
                None, None, None, None, None, "")

    # Edit mode — pattern-match button
    if isinstance(triggered, dict) and triggered.get("type") == "roadmap-dep-edit-btn":
        dep_id = triggered["index"]
        token = get_user_token()
        dep_df = dependency_service.get_dependency(dep_id, user_token=token)
        if dep_df.empty:
            return (no_update,) * 9
        dep = dep_df.iloc[0]
        stored = {"dependency_id": dep_id, "updated_at": str(dep.get("updated_at", ""))}
        return (
            True, f"Edit Dependency — {dep_id}", json.dumps(stored),
            dep.get("source_project_id"),
            dep.get("target_project_id"),
            dep.get("dependency_type"),
            dep.get("risk_level"),
            dep.get("status"),
            dep.get("description", ""),
        )

    return (no_update,) * 9


@callback(
    Output("roadmap-dep-modal", "is_open", allow_duplicate=True),
    Output("roadmap-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    *modal_error_outputs("roadmap-dep", DEP_FIELDS),
    Input("roadmap-dep-save-btn", "n_clicks"),
    State("roadmap-selected-dep-store", "data"),
    State("roadmap-mutation-counter", "data"),
    *modal_field_states("roadmap-dep", DEP_FIELDS),
    prevent_initial_call=True,
)
def save_dependency(n_clicks, stored_dep, counter, *field_values):
    """Save (create or update) a dependency."""
    form_data = get_modal_values("roadmap-dep", DEP_FIELDS, *field_values)

    token = get_user_token()
    email = get_user_email()

    if stored_dep:
        stored = json.loads(stored_dep) if isinstance(stored_dep, str) else stored_dep
        dep_id = stored["dependency_id"]
        expected = stored.get("updated_at", "")
        result = dependency_service.update_dependency_from_form(
            dep_id, form_data, expected,
            user_email=email, user_token=token,
        )
    else:
        result = dependency_service.create_dependency_from_form(
            form_data, user_email=email, user_token=token,
        )

    if result["success"]:
        no_errors = set_field_errors("roadmap-dep", DEP_FIELDS, {})
        error_outputs = []
        for inv, fb in zip(no_errors[0], no_errors[1]):
            error_outputs.extend([inv, fb])
        return (False, (counter or 0) + 1, result["message"], "Success", "success", True,
                *error_outputs)

    errors = result.get("errors", {})
    field_errors = set_field_errors("roadmap-dep", DEP_FIELDS, errors)
    error_outputs = []
    for inv, fb in zip(field_errors[0], field_errors[1]):
        error_outputs.extend([inv, fb])
    return (True, no_update, result["message"], "Error", "danger", True,
            *error_outputs)


@callback(
    Output("roadmap-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input({"type": "roadmap-dep-status-dd", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def change_dep_status(status_values):
    """Update dependency status when inline dropdown changes."""
    triggered = ctx.triggered
    if not triggered or triggered[0]["value"] is None:
        return (no_update,) * 5

    prop_id = triggered[0]["prop_id"]
    try:
        id_dict = json.loads(prop_id.rsplit(".", 1)[0])
        dep_id = id_dict["index"]
    except (json.JSONDecodeError, KeyError):
        return (no_update,) * 5

    new_status = triggered[0]["value"]
    valid_statuses = {o["value"] for o in DEP_STATUS_OPTIONS}
    if new_status not in valid_statuses:
        return no_update, "Invalid status", "Error", "danger", True

    token = get_user_token()
    email = get_user_email()

    result = dependency_service.update_dependency_status(
        dep_id, new_status, user_email=email, user_token=token,
    )
    if result["success"]:
        return 1, result["message"], "Status Updated", "success", True
    return no_update, result["message"], "Error", "danger", True


@callback(
    Output("roadmap-dep-delete-modal", "is_open", allow_duplicate=True),
    Output("roadmap-dep-delete-target-store", "data", allow_duplicate=True),
    Input({"type": "roadmap-dep-delete-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_delete_modal(n_clicks_list):
    """Open delete confirmation with the dependency ID."""
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        return no_update, no_update
    dep_id = triggered["index"]
    return True, dep_id


@callback(
    Output("roadmap-dep-delete-modal", "is_open", allow_duplicate=True),
    Output("roadmap-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input("roadmap-dep-delete-confirm-btn", "n_clicks"),
    State("roadmap-dep-delete-target-store", "data"),
    State("roadmap-mutation-counter", "data"),
    prevent_initial_call=True,
)
def confirm_delete_dep(n_clicks, dep_id, counter):
    """Soft-delete the dependency."""
    if not dep_id:
        return no_update, no_update, no_update, no_update, no_update, no_update

    token = get_user_token()
    email = get_user_email()
    success = dependency_service.delete_dependency(dep_id, user_email=email, user_token=token)

    if success:
        return False, (counter or 0) + 1, "Dependency deleted", "Deleted", "success", True
    return False, no_update, "Failed to delete dependency", "Error", "danger", True


@callback(
    Output("roadmap-dep-modal", "is_open", allow_duplicate=True),
    Input("roadmap-dep-cancel-btn", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_dep_modal(n):
    """Close dependency modal on cancel."""
    return False


@callback(
    Output("roadmap-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input({"type": "roadmap-dep-resolve-btn", "index": ALL}, "n_clicks"),
    State("roadmap-mutation-counter", "data"),
    prevent_initial_call=True,
)
def resolve_dep_action(n_clicks_list, counter):
    """Mark a dependency as resolved."""
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        return (no_update,) * 5

    dep_id = triggered["index"]
    token = get_user_token()
    email = get_user_email()

    result = dependency_service.resolve_dependency(dep_id, user_email=email, user_token=token)
    if result["success"]:
        return (counter or 0) + 1, result["message"], "Resolved", "success", True
    return no_update, result["message"], "Error", "danger", True
