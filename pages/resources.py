"""
Resource Allocation Page — Team Management & Capacity Planning
================================================================
Team workload overview, project assignments CRUD, capacity bar chart
with over-allocation warnings, and utilization details.
"""

import json
import dash
from dash import html, dcc, callback, Input, Output, State, ctx, ALL, no_update
import dash_bootstrap_components as dbc
from services.auth_service import get_user_token, get_user_email
from services.analytics_service import get_resource_allocations
from services import resource_service
from components.kpi_card import kpi_card
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from components.crud_modal import (
    crud_modal, confirm_delete_modal, get_modal_values,
    set_field_errors, modal_field_states, modal_error_outputs,
)
from components.filter_bar import filter_bar
from charts.theme import COLORS
from charts.analytics_charts import resource_utilization_chart

dash.register_page(__name__, path="/resources", name="Resource Allocation")

# ── Role display options ────────────────────────────────────────────

PROJECT_ROLE_OPTIONS = [
    {"label": "PM", "value": "pm"},
    {"label": "Lead", "value": "lead"},
    {"label": "Engineer", "value": "engineer"},
    {"label": "Analyst", "value": "analyst"},
    {"label": "Stakeholder", "value": "stakeholder"},
]

PROJECT_ROLE_COLORS = {
    "pm": "primary",
    "lead": "info",
    "engineer": "success",
    "analyst": "warning",
    "stakeholder": "secondary",
}

# ── CRUD Modal Field Definitions ────────────────────────────────────

ASSIGNMENT_FIELDS = [
    {"id": "user_id", "label": "Team Member", "type": "select", "required": True,
     "options": [], "placeholder": "Select member..."},
    {"id": "project_id", "label": "Project", "type": "select", "required": True,
     "options": [], "placeholder": "Select project..."},
    {"id": "project_role", "label": "Role", "type": "select", "required": True,
     "options": PROJECT_ROLE_OPTIONS},
    {"id": "allocation_pct", "label": "Allocation %", "type": "number",
     "required": True, "min": 0, "max": 100, "placeholder": "e.g. 50"},
    {"id": "start_date", "label": "Start Date", "type": "date", "required": False},
    {"id": "end_date", "label": "End Date", "type": "date", "required": False},
]

# ── Filter definitions ──────────────────────────────────────────────

RESOURCES_FILTERS = [
    {"id": "role", "label": "Role", "type": "select", "multi": True,
     "options": [{"label": "Lead", "value": "lead"},
                 {"label": "Engineer", "value": "engineer"},
                 {"label": "Analyst", "value": "analyst"},
                 {"label": "Viewer", "value": "viewer"}]},
]


# ── Helper functions ────────────────────────────────────────────────


def _allocation_bar_color(pct):
    """Return bar color based on allocation percentage."""
    if pct > 100:
        return COLORS["red"]
    elif pct >= 80:
        return COLORS["yellow"]
    return COLORS["green"]


def _build_capacity_chart(capacity_df):
    """Build a horizontal bar chart showing total allocation per member."""
    import plotly.graph_objects as go
    from charts.theme import apply_theme

    if capacity_df.empty or "total_allocation" not in capacity_df.columns:
        return None

    names = capacity_df["display_name"].tolist()
    allocations = capacity_df["total_allocation"].tolist()
    colors = [_allocation_bar_color(a) for a in allocations]

    fig = go.Figure(go.Bar(
        y=names,
        x=allocations,
        orientation="h",
        marker=dict(color=colors),
        hovertemplate="<b>%{y}</b><br>%{x}% allocated<extra></extra>",
    ))
    fig.update_layout(
        xaxis=dict(title="Total Allocation %", range=[0, max(max(allocations, default=0) + 20, 130)], dtick=25),
        height=max(200, len(names) * 50),
    )
    fig.add_vline(
        x=100, line=dict(color=COLORS["red"], width=1, dash="dash"),
        annotation_text="100%", annotation_font=dict(size=10, color=COLORS["red"]),
    )
    return apply_theme(fig)


def _build_content(role_filter=None, department_id=None):
    """Build the actual page content."""
    token = get_user_token()
    resources = get_resource_allocations(user_token=token)

    # Get capacity overview
    capacity = resource_service.get_capacity_overview(
        department_id=department_id, user_token=token,
    )

    # Apply role filter on resource allocations
    if not resources.empty and role_filter and "role" in resources.columns:
        resources = resources[resources["role"].isin(role_filter)]

    # Compute KPIs
    if not capacity.empty and "total_allocation" in capacity.columns:
        team_size = len(capacity)
        avg_alloc = capacity["total_allocation"].mean()
        over_allocated = len(capacity[capacity["total_allocation"] > 100])
        available = len(capacity[capacity["total_allocation"] < 80])
    elif not resources.empty:
        team_size = resources["display_name"].nunique()
        avg_alloc = 0
        over_allocated = 0
        available = team_size
    else:
        team_size = 0
        avg_alloc = 0
        over_allocated = 0
        available = 0

    # Build capacity chart
    capacity_fig = _build_capacity_chart(capacity) if not capacity.empty else None

    # Build project assignment table rows
    assignment_rows = []
    if not resources.empty:
        for _, row in resources.iterrows():
            uid = row.get("user_id", "")
            pid = row.get("project_id", "")
            alloc = row.get("allocation_pct", 0)

            alloc_color = COLORS["red"] if alloc and int(alloc) > 100 else (
                COLORS["yellow"] if alloc and int(alloc) >= 80 else COLORS["text"])

            assignment_rows.append(html.Tr([
                html.Td([
                    html.Div(row.get("display_name", "Unknown"), className="fw-bold small"),
                    html.Small(row.get("role", "").title(), className="text-muted"),
                ]),
                html.Td(html.Small(row.get("project_name", "N/A"))),
                html.Td(str(row.get("task_count", 0)), className="text-center"),
                html.Td(str(row.get("points_assigned", 0)), className="text-center"),
                html.Td(str(row.get("points_done", 0)), className="text-center"),
                html.Td(
                    html.Span(
                        f"{alloc}%" if alloc else "—",
                        style={"color": alloc_color, "fontWeight": "bold"} if alloc else {},
                    ),
                    className="text-center",
                ),
                html.Td(
                    dbc.Progress(
                        value=(row.get("points_done", 0) / max(row.get("points_assigned", 1), 1) * 100),
                        style={"height": "8px"},
                        color="success",
                    ),
                ),
            ]))

    # Build over-allocation warnings
    over_alloc_warnings = []
    if not capacity.empty and "total_allocation" in capacity.columns:
        over_members = capacity[capacity["total_allocation"] > 100]
        for _, m in over_members.iterrows():
            over_alloc_warnings.append(
                dbc.Alert(
                    [
                        html.I(className="bi bi-exclamation-triangle-fill me-2"),
                        html.Strong(m["display_name"]),
                        f" is over-allocated at {int(m['total_allocation'])}%",
                    ],
                    color="danger",
                    className="py-2 mb-2",
                )
            )

    return html.Div([
        html.H4("Resource Allocation", className="page-title mb-3"),
        html.P(
            "Team workload distribution, project assignments, capacity planning, "
            "and over-allocation warnings.",
            className="page-subtitle mb-4",
        ),

        # KPI strip
        dbc.Row([
            dbc.Col(kpi_card("Team Size", team_size, "active members"), width=3),
            dbc.Col(kpi_card("Avg Allocation", f"{avg_alloc:.0f}%",
                             "across all members"), width=3),
            dbc.Col(kpi_card("Over-Allocated", over_allocated, "> 100%",
                             COLORS["red"] if over_allocated > 0 else None), width=3),
            dbc.Col(kpi_card("Available Capacity", available, "< 80% allocated",
                             COLORS["green"] if available > 0 else None), width=3),
        ], className="kpi-strip mb-4"),

        # Over-allocation warnings
        html.Div(over_alloc_warnings, className="mb-3") if over_alloc_warnings else html.Div(),

        # Capacity chart + utilization chart
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Capacity Planning — Total Allocation per Member"),
                    dbc.CardBody(
                        dcc.Graph(
                            figure=capacity_fig,
                            config={"displayModeBar": False},
                        ) if capacity_fig else empty_state("No capacity data.")
                    ),
                ], className="chart-card"),
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Team Utilization — By Project"),
                    dbc.CardBody(
                        dcc.Graph(
                            figure=resource_utilization_chart(resources),
                            config={"displayModeBar": False},
                        ) if not resources.empty else empty_state("No resource data.")
                    ),
                ], className="chart-card"),
            ], width=6),
        ], className="mb-4"),

        # Team member detail table
        dbc.Card([
            dbc.CardHeader("Team Assignments"),
            dbc.CardBody([
                dbc.Table([
                    html.Thead(html.Tr([
                        html.Th("Name"),
                        html.Th("Project"),
                        html.Th("Tasks", className="text-center"),
                        html.Th("Points", className="text-center"),
                        html.Th("Done", className="text-center"),
                        html.Th("Alloc %", className="text-center"),
                        html.Th("Progress"),
                    ])),
                    html.Tbody(assignment_rows),
                ], bordered=False, hover=True, responsive=True,
                    className="table-dark table-sm"),
            ] if assignment_rows else [empty_state("No team data available.")]),
        ]),
    ])


# ── Layout ──────────────────────────────────────────────────────────


def layout():
    return html.Div([
        # Stores
        dcc.Store(id="resources-mutation-counter", data=0),
        dcc.Store(id="resources-selected-assignment-store", data=None),

        # Toolbar row
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    [html.I(className="bi bi-plus-circle me-1"), "Assign Member"],
                    id="resources-add-assignment-btn", color="primary", size="sm",
                    className="me-2",
                ),
            ], className="d-flex align-items-start justify-content-end"),
        ], className="mb-3"),

        # Filters
        filter_bar("resources", RESOURCES_FILTERS),

        # Content area
        html.Div(id="resources-content"),
        auto_refresh(interval_id="resources-refresh-interval"),

        # Modals
        crud_modal("resources-assignment", "Assign Team Member", ASSIGNMENT_FIELDS, size="lg"),
        confirm_delete_modal("resources-assignment", "assignment"),
    ])


# ── Callbacks ───────────────────────────────────────────────────────


@callback(
    Output("resources-content", "children"),
    Input("resources-refresh-interval", "n_intervals"),
    Input("resources-mutation-counter", "data"),
    Input("resources-role-filter", "value"),
    Input("active-department-store", "data"),
)
def refresh_resources(n, mutation_count, role_filter, department_id):
    """Refresh resource content on interval, mutation, or filter change."""
    return _build_content(
        role_filter=role_filter,
        department_id=department_id,
    )


@callback(
    Output("resources-assignment-modal", "is_open", allow_duplicate=True),
    Output("resources-assignment-modal-title", "children", allow_duplicate=True),
    Output("resources-selected-assignment-store", "data", allow_duplicate=True),
    Output("resources-assignment-user_id", "value", allow_duplicate=True),
    Output("resources-assignment-project_id", "value", allow_duplicate=True),
    Output("resources-assignment-project_role", "value", allow_duplicate=True),
    Output("resources-assignment-allocation_pct", "value", allow_duplicate=True),
    Output("resources-assignment-start_date", "value", allow_duplicate=True),
    Output("resources-assignment-end_date", "value", allow_duplicate=True),
    Output("resources-assignment-user_id", "options"),
    Output("resources-assignment-project_id", "options"),
    Input("resources-add-assignment-btn", "n_clicks"),
    prevent_initial_call=True,
)
def open_assignment_modal(add_clicks):
    """Open assignment modal for create (blank) with dynamically loaded options."""
    token = get_user_token()

    # Load team members for dropdown
    members = resource_service.get_team_members(user_token=token)
    member_options = []
    if not members.empty:
        for _, m in members.iterrows():
            member_options.append({
                "label": f"{m['display_name']} ({m.get('role', '').title()})",
                "value": m["user_id"],
            })

    # Load projects for dropdown
    from services.project_service import get_projects
    projects = get_projects(user_token=token)
    project_options = []
    if not projects.empty:
        for _, p in projects.iterrows():
            project_options.append({
                "label": p.get("name", p.get("project_id", "")),
                "value": p["project_id"],
            })

    return (
        True, "Assign Team Member", None,
        None, None, None, None, None, None,
        member_options, project_options,
    )


@callback(
    Output("resources-assignment-modal", "is_open", allow_duplicate=True),
    Output("resources-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    *modal_error_outputs("resources-assignment", ASSIGNMENT_FIELDS),
    Input("resources-assignment-save-btn", "n_clicks"),
    State("resources-selected-assignment-store", "data"),
    State("resources-mutation-counter", "data"),
    *modal_field_states("resources-assignment", ASSIGNMENT_FIELDS),
    prevent_initial_call=True,
)
def save_assignment(n_clicks, stored_assignment, counter, *field_values):
    """Save (create or update) an assignment."""
    form_data = get_modal_values("resources-assignment", ASSIGNMENT_FIELDS, *field_values)

    token = get_user_token()
    email = get_user_email()

    if stored_assignment:
        stored = json.loads(stored_assignment) if isinstance(stored_assignment, str) else stored_assignment
        project_id = stored["project_id"]
        user_id = stored["user_id"]
        expected = stored.get("updated_at", "")
        result = resource_service.update_assignment(
            project_id, user_id, form_data, expected,
            user_email=email, user_token=token,
        )
    else:
        result = resource_service.assign_member_to_project(
            form_data, user_email=email, user_token=token,
        )

    if result["success"]:
        no_errors = set_field_errors("resources-assignment", ASSIGNMENT_FIELDS, {})
        error_outputs = []
        for inv, fb in zip(no_errors[0], no_errors[1]):
            error_outputs.extend([inv, fb])
        return (False, (counter or 0) + 1, result["message"], "Success", "success", True,
                *error_outputs)

    errors = result.get("errors", {})
    field_errors = set_field_errors("resources-assignment", ASSIGNMENT_FIELDS, errors)
    error_outputs = []
    for inv, fb in zip(field_errors[0], field_errors[1]):
        error_outputs.extend([inv, fb])
    return (True, no_update, result["message"], "Error", "danger", True,
            *error_outputs)


@callback(
    Output("resources-assignment-modal", "is_open", allow_duplicate=True),
    Input("resources-assignment-cancel-btn", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_assignment_modal(n):
    """Close assignment modal on cancel."""
    return False
