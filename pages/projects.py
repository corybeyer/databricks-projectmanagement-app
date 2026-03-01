"""
All Projects Page -- Full CRUD
===============================
Project list with health badges, progress bars, key metrics,
and create/edit/delete via CRUD modal.
"""

import json
import dash
from dash import html, dcc, callback, Input, Output, State, ctx, ALL, no_update
import dash_bootstrap_components as dbc
from services.auth_service import (
    get_user_token, get_user_email, get_current_user, has_permission,
)
from services import project_service
from components.health_badge import health_badge
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from components.crud_modal import (
    crud_modal, confirm_delete_modal, get_modal_values,
    set_field_errors, modal_field_states, modal_error_outputs,
)
from charts.theme import COLORS
from utils.url_state import get_param, set_params
from components.filter_bar import filter_bar, sort_toggle
from components.export_button import export_button

dash.register_page(__name__, path="/projects", name="All Projects")

# -- CRUD Modal Field Definitions -----------------------------------

PROJECT_FIELDS = [
    {"id": "name", "label": "Project Name", "type": "text", "required": True,
     "placeholder": "Enter project name"},
    {"id": "delivery_method", "label": "Delivery Method", "type": "select", "required": True,
     "options": [{"label": "Waterfall", "value": "waterfall"},
                 {"label": "Agile", "value": "agile"},
                 {"label": "Hybrid", "value": "hybrid"}]},
    {"id": "status", "label": "Status", "type": "select", "required": True,
     "options": [{"label": "Planning", "value": "planning"},
                 {"label": "Active", "value": "active"},
                 {"label": "On Hold", "value": "on_hold"},
                 {"label": "Completed", "value": "completed"}]},
    {"id": "health", "label": "Health", "type": "select", "required": True,
     "options": [{"label": "On Track", "value": "green"},
                 {"label": "At Risk", "value": "yellow"},
                 {"label": "Off Track", "value": "red"}]},
    {"id": "owner", "label": "Owner", "type": "text", "required": True,
     "placeholder": "Project owner"},
    {"id": "start_date", "label": "Start Date", "type": "date", "required": True},
    {"id": "target_date", "label": "Target Date", "type": "date", "required": False},
    {"id": "budget_total", "label": "Budget ($)", "type": "number", "required": False,
     "placeholder": "Total budget"},
    {"id": "description", "label": "Description", "type": "textarea", "required": False,
     "rows": 3},
]


# -- Helper functions -----------------------------------------------


def _project_card(project):
    """Render a project summary card with edit/delete buttons."""
    pct = project.get("pct_complete", 0) or 0
    budget_total = max(project.get("budget_total", 1) or 1, 1)
    budget_pct = (project.get("budget_spent", 0) or 0) / budget_total * 100
    project_id = project.get("project_id", "")

    return dbc.Col([
        dbc.Card([
            dbc.CardHeader([
                html.Div([
                    html.Div(project["name"], className="fw-bold"),
                    health_badge(project.get("health", "green")),
                ], className="d-flex justify-content-between align-items-center"),
            ]),
            dbc.CardBody([
                html.Div([
                    html.Small("Method", className="text-muted d-block"),
                    html.Span(
                        (project.get("delivery_method") or "N/A").title(),
                        className="badge bg-secondary",
                    ),
                ], className="mb-2"),
                html.Div([
                    html.Small("Owner", className="text-muted d-block"),
                    html.Span(project.get("owner") or "Unassigned"),
                ], className="mb-2"),
                html.Div([
                    html.Small("Phase", className="text-muted d-block"),
                    html.Span(project.get("current_phase_name", "N/A")),
                ], className="mb-2"),
                html.Div([
                    html.Small("Sprint", className="text-muted d-block"),
                    html.Span(project.get("active_sprint_name") or "None"),
                ], className="mb-3"),
                html.Div([
                    html.Div(
                        f"Completion: {pct:.0f}%",
                        className="small text-muted mb-1",
                    ),
                    dbc.Progress(
                        value=pct,
                        color="success" if pct >= 70 else "warning" if pct >= 40 else "info",
                        style={"height": "8px"},
                    ),
                ], className="mb-2"),
                html.Div([
                    html.Div(
                        f"Budget: {budget_pct:.0f}% spent",
                        className="small text-muted mb-1",
                    ),
                    dbc.Progress(
                        value=budget_pct,
                        color="danger" if budget_pct > 90 else "warning" if budget_pct > 75 else "success",
                        style={"height": "8px"},
                    ),
                ]),
            ]),
            dbc.CardFooter([
                html.Div([
                    html.Small(
                        f"${project.get('budget_spent', 0) or 0:,.0f} / "
                        f"${project.get('budget_total', 0) or 0:,.0f}",
                        className="text-muted",
                    ),
                    html.Div([
                        dbc.Button(
                            html.I(className="bi bi-pencil-square"),
                            id={"type": "projects-project-edit-btn", "index": project_id},
                            size="sm", color="link", className="p-0 me-2 text-muted",
                        ),
                        dbc.Button(
                            html.I(className="bi bi-trash"),
                            id={"type": "projects-project-delete-btn", "index": project_id},
                            size="sm", color="link", className="p-0 text-muted",
                        ),
                    ], className="d-flex align-items-center"),
                ], className="d-flex justify-content-between align-items-center"),
            ]),
        ], className="project-card h-100"),
    ], width=4, className="mb-3")


def _build_content(portfolio_id=None, status_filter=None, health_filter=None,
                   method_filter=None, sort_by=None):
    """Build the actual page content."""
    token = get_user_token()
    projects = project_service.get_projects(
        portfolio_id=portfolio_id, user_token=token,
    )

    # Filter out deleted
    if not projects.empty and "is_deleted" in projects.columns:
        projects = projects[projects["is_deleted"] == False]  # noqa: E712

    # Apply filters
    if not projects.empty and status_filter:
        projects = projects[projects["status"].isin(status_filter)]
    if not projects.empty and health_filter:
        projects = projects[projects["health"].isin(health_filter)]
    if not projects.empty and method_filter and "delivery_method" in projects.columns:
        projects = projects[projects["delivery_method"].isin(method_filter)]

    # Apply sort
    if not projects.empty and sort_by:
        if sort_by == "name":
            projects = projects.sort_values("name")
        elif sort_by == "health":
            health_order = {"red": 0, "yellow": 1, "green": 2}
            projects = projects.assign(
                _health_ord=projects["health"].map(health_order)
            ).sort_values("_health_ord").drop(columns=["_health_ord"])
        elif sort_by == "completion":
            projects = projects.sort_values("pct_complete", ascending=False)

    total = len(projects)
    if not projects.empty:
        green_count = len(projects[projects["health"] == "green"])
        yellow_count = len(projects[projects["health"] == "yellow"])
        red_count = len(projects[projects["health"] == "red"])
    else:
        green_count = yellow_count = red_count = 0

    return html.Div([
        html.Div([
            html.Div(html.I(className="bi bi-kanban-fill"), className="page-header-icon"),
            html.H4("All Projects", className="page-title"),
        ], className="page-header mb-3"),
        html.P(
            "Overview of all active projects across portfolios with status, "
            "health, and budget tracking.",
            className="page-subtitle mb-4",
        ),

        # Summary stats
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Span(str(total), className="fs-4 fw-bold me-2"),
                    html.Span("projects", className="text-muted"),
                ]),
            ], width="auto"),
            dbc.Col([
                html.Div([
                    html.Span("* ", style={"color": COLORS["green"]}),
                    html.Span(
                        f"{green_count} on track",
                        className="text-muted me-3",
                    ),
                    html.Span("* ", style={"color": COLORS["yellow"]}),
                    html.Span(
                        f"{yellow_count} at risk",
                        className="text-muted me-3",
                    ),
                    html.Span("* ", style={"color": COLORS["red"]}),
                    html.Span(
                        f"{red_count} off track",
                        className="text-muted",
                    ),
                ]) if not projects.empty else html.Span(),
            ]),
        ], className="mb-4 align-items-center"),

        # Project cards grid
        dbc.Row([
            _project_card(row.to_dict())
            for _, row in projects.iterrows()
        ] if not projects.empty else [
            dbc.Col(empty_state("No projects found. Create one to get started."), width=12),
        ]),
    ])


# -- Layout ----------------------------------------------------------


PROJECTS_FILTERS = [
    {"id": "status", "label": "Status", "type": "select", "multi": True,
     "options": [{"label": "Planning", "value": "planning"},
                 {"label": "Active", "value": "active"},
                 {"label": "On Hold", "value": "on_hold"},
                 {"label": "Completed", "value": "completed"}]},
    {"id": "health", "label": "Health", "type": "select", "multi": True,
     "options": [{"label": "On Track", "value": "green"},
                 {"label": "At Risk", "value": "yellow"},
                 {"label": "Off Track", "value": "red"}]},
    {"id": "method", "label": "Method", "type": "select", "multi": True,
     "options": [{"label": "Waterfall", "value": "waterfall"},
                 {"label": "Agile", "value": "agile"},
                 {"label": "Hybrid", "value": "hybrid"}]},
]

PROJECTS_SORT_OPTIONS = [
    {"label": "Name", "value": "name"},
    {"label": "Health", "value": "health"},
    {"label": "Completion %", "value": "completion"},
]


def layout():
    user = get_current_user()
    can_write = has_permission(user, "create", "project")
    return html.Div([
        # Stores
        dcc.Store(id="projects-mutation-counter", data=0),
        dcc.Store(id="projects-selected-project-store", data=None),

        # Toolbar
        dbc.Row([
            dbc.Col([], width=8),
            dbc.Col([
                dbc.Button(
                    [html.I(className="bi bi-plus-circle me-1"), "New Project"],
                    id="projects-add-project-btn", color="primary", size="sm",
                    style={"display": "inline-block" if can_write else "none"},
                    className="me-2",
                ),
                export_button("projects-export-btn", "Export"),
            ], width=4, className="d-flex align-items-start justify-content-end"),
        ], className="mb-3"),

        # Filters
        filter_bar("projects", PROJECTS_FILTERS),
        sort_toggle("projects", PROJECTS_SORT_OPTIONS),

        # Content area
        html.Div(id="projects-content"),
        auto_refresh(interval_id="projects-refresh-interval"),

        # Modals
        crud_modal("projects-project", "Create Project", PROJECT_FIELDS, size="lg"),
        confirm_delete_modal("projects-project", "project"),
    ])


# -- Callbacks -------------------------------------------------------


@callback(
    Output("projects-content", "children"),
    Input("projects-refresh-interval", "n_intervals"),
    Input("projects-mutation-counter", "data"),
    Input("url", "search"),
    Input("projects-status-filter", "value"),
    Input("projects-health-filter", "value"),
    Input("projects-method-filter", "value"),
    Input("projects-sort-toggle", "value"),
)
def refresh_projects(n, mutation_count, search, status_filter,
                     health_filter, method_filter, sort_by):
    """Refresh project content on interval, mutation, or filter change."""
    portfolio_id = get_param(search, "portfolio_id") if search else None
    return _build_content(
        portfolio_id=portfolio_id,
        status_filter=status_filter,
        health_filter=health_filter,
        method_filter=method_filter,
        sort_by=sort_by,
    )


@callback(
    Output("projects-project-modal", "is_open", allow_duplicate=True),
    Output("projects-project-modal-title", "children", allow_duplicate=True),
    Output("projects-selected-project-store", "data", allow_duplicate=True),
    Output("projects-project-name", "value", allow_duplicate=True),
    Output("projects-project-delivery_method", "value", allow_duplicate=True),
    Output("projects-project-status", "value", allow_duplicate=True),
    Output("projects-project-health", "value", allow_duplicate=True),
    Output("projects-project-owner", "value", allow_duplicate=True),
    Output("projects-project-start_date", "value", allow_duplicate=True),
    Output("projects-project-target_date", "value", allow_duplicate=True),
    Output("projects-project-budget_total", "value", allow_duplicate=True),
    Output("projects-project-description", "value", allow_duplicate=True),
    Input("projects-add-project-btn", "n_clicks"),
    Input({"type": "projects-project-edit-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def toggle_project_modal(add_clicks, edit_clicks):
    """Open project modal for create (blank) or edit (populated)."""
    # Guard: ignore when fired by new components appearing (no actual click)
    triggered = ctx.triggered
    if not triggered or all(t.get("value") is None or t.get("value") == 0 for t in triggered):
        return (no_update,) * 12

    triggered_id = ctx.triggered_id

    # Create mode
    if triggered_id == "projects-add-project-btn" and add_clicks:
        return (True, "Create Project", None,
                "", None, None, None, "", None, None, None, "")

    # Edit mode -- pattern-match button
    if isinstance(triggered_id, dict) and triggered_id.get("type") == "projects-project-edit-btn":
        project_id = triggered_id["index"]
        token = get_user_token()
        project_df = project_service.get_project(project_id, user_token=token)
        if project_df.empty:
            return (no_update,) * 12
        p = project_df.iloc[0]
        stored = {"project_id": project_id, "updated_at": str(p.get("updated_at", ""))}
        return (
            True, f"Edit Project -- {p.get('name', project_id)}",
            json.dumps(stored),
            p.get("name", ""),
            p.get("delivery_method"),
            p.get("status"),
            p.get("health"),
            p.get("owner", ""),
            p.get("start_date", ""),
            p.get("target_date", ""),
            p.get("budget_total"),
            p.get("description", ""),
        )

    return (no_update,) * 12


@callback(
    Output("projects-project-modal", "is_open", allow_duplicate=True),
    Output("projects-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    *modal_error_outputs("projects-project", PROJECT_FIELDS),
    Input("projects-project-save-btn", "n_clicks"),
    State("projects-selected-project-store", "data"),
    State("projects-mutation-counter", "data"),
    *modal_field_states("projects-project", PROJECT_FIELDS),
    prevent_initial_call=True,
)
def save_project(n_clicks, stored_project, counter, *field_values):
    """Save (create or update) a project."""
    if not n_clicks:
        return (no_update,) * (6 + len(PROJECT_FIELDS) * 2)
    form_data = get_modal_values("projects-project", PROJECT_FIELDS, *field_values)

    token = get_user_token()
    email = get_user_email()

    if stored_project:
        stored = json.loads(stored_project) if isinstance(stored_project, str) else stored_project
        project_id = stored["project_id"]
        expected = stored.get("updated_at", "")
        result = project_service.update_project_from_form(
            project_id, form_data, expected,
            user_email=email, user_token=token,
        )
    else:
        result = project_service.create_project_from_form(
            form_data, user_email=email, user_token=token,
        )

    if result["success"]:
        no_errors = set_field_errors("projects-project", PROJECT_FIELDS, {})
        error_outputs = []
        for inv, fb in zip(no_errors[0], no_errors[1]):
            error_outputs.extend([inv, fb])
        return (False, (counter or 0) + 1, result["message"], "Success", "success", True,
                *error_outputs)

    errors = result.get("errors", {})
    field_errors = set_field_errors("projects-project", PROJECT_FIELDS, errors)
    error_outputs = []
    for inv, fb in zip(field_errors[0], field_errors[1]):
        error_outputs.extend([inv, fb])
    return (True, no_update, result["message"], "Error", "danger", True,
            *error_outputs)


@callback(
    Output("projects-project-delete-modal", "is_open", allow_duplicate=True),
    Output("projects-project-delete-target-store", "data", allow_duplicate=True),
    Input({"type": "projects-project-delete-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_delete_modal(n_clicks_list):
    """Open delete confirmation with the project ID."""
    triggered = ctx.triggered
    if not triggered or all(t.get("value") is None or t.get("value") == 0 for t in triggered):
        return no_update, no_update
    triggered_id = ctx.triggered_id
    if not isinstance(triggered_id, dict):
        return no_update, no_update
    project_id = triggered_id["index"]
    return True, project_id


@callback(
    Output("projects-project-delete-modal", "is_open", allow_duplicate=True),
    Output("projects-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input("projects-project-delete-confirm-btn", "n_clicks"),
    State("projects-project-delete-target-store", "data"),
    State("projects-mutation-counter", "data"),
    prevent_initial_call=True,
)
def confirm_delete_project(n_clicks, project_id, counter):
    """Soft-delete the project."""
    if not n_clicks:
        return (no_update,) * 6
    if not project_id:
        return no_update, no_update, no_update, no_update, no_update, no_update

    token = get_user_token()
    email = get_user_email()
    success = project_service.delete_project(project_id, user_email=email, user_token=token)

    if success:
        return False, (counter or 0) + 1, "Project deleted", "Deleted", "success", True
    return False, no_update, "Failed to delete project", "Error", "danger", True


@callback(
    Output("projects-project-modal", "is_open", allow_duplicate=True),
    Input("projects-project-cancel-btn", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_project_modal(n):
    """Close project modal on cancel."""
    return False


@callback(
    Output("projects-export-btn-download", "data"),
    Input("projects-export-btn", "n_clicks"),
    prevent_initial_call=True,
)
def export_projects(n_clicks):
    """Export project data to Excel."""
    if not n_clicks:
        return no_update
    from datetime import datetime
    from services import export_service
    token = get_user_token()
    df = project_service.get_projects(user_token=token)
    excel_bytes = export_service.to_excel(df, "projects")
    return dcc.send_bytes(excel_bytes, f"projects_{datetime.now().strftime('%Y%m%d')}.xlsx")
