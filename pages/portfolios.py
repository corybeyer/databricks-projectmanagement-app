"""
Portfolios Page -- Full CRUD
=============================
Portfolio list with drill-down, budget burn chart, strategic bubble chart,
and create/edit/delete via CRUD modal.
"""

import json
import dash
from dash import html, dcc, callback, Input, Output, State, ctx, ALL, no_update
import dash_bootstrap_components as dbc
from services.auth_service import get_user_token, get_user_email
from services.portfolio_service import (
    get_dashboard_data, get_portfolio_projects, get_portfolio,
    create_portfolio_from_form, update_portfolio_from_form, delete_portfolio,
)
from components.kpi_card import kpi_card
from components.health_badge import health_badge
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from components.crud_modal import (
    crud_modal, confirm_delete_modal, get_modal_values,
    set_field_errors, modal_field_states, modal_error_outputs,
)
from charts.theme import COLORS
from charts.portfolio_charts import budget_burn_chart, strategic_bubble_chart
from utils.url_state import get_param

dash.register_page(__name__, path="/portfolios", name="Portfolios")

# -- CRUD Modal Field Definitions -----------------------------------

PORTFOLIO_FIELDS = [
    {"id": "name", "label": "Portfolio Name", "type": "text", "required": True,
     "placeholder": "Enter portfolio name"},
    {"id": "owner", "label": "Owner", "type": "text", "required": True,
     "placeholder": "Portfolio owner"},
    {"id": "description", "label": "Description", "type": "textarea", "required": False,
     "rows": 3},
    {"id": "strategic_priority", "label": "Strategic Priority", "type": "text",
     "required": False, "placeholder": "Strategic alignment"},
]


# -- Helper functions -----------------------------------------------


def _project_row(project):
    """Render a single project row inside a portfolio."""
    pct = project.get("pct_complete", 0) or 0
    return dbc.ListGroupItem([
        dbc.Row([
            dbc.Col([
                html.Div(project["name"], className="fw-bold"),
                html.Small(
                    f"{(project.get('delivery_method') or 'N/A')} · "
                    f"{project.get('current_phase_name', 'N/A')}",
                    className="text-muted",
                ),
            ], width=5),
            dbc.Col([
                dbc.Progress(
                    value=pct, label=f"{pct:.0f}%",
                    color="success" if pct >= 70 else "warning" if pct >= 40 else "info",
                    className="my-1",
                    style={"height": "18px"},
                ),
            ], width=4),
            dbc.Col([
                health_badge(project.get("health", "green")),
            ], width=3, className="text-end"),
        ], align="center"),
    ], className="bg-transparent border-secondary")


def _build_content(department_id=None):
    """Build the actual page content."""
    token = get_user_token()
    data = get_dashboard_data(department_id=department_id, user_token=token)
    portfolios = data["portfolios"]

    # Filter out deleted
    if not portfolios.empty and "is_deleted" in portfolios.columns:
        portfolios = portfolios[portfolios["is_deleted"] == False]  # noqa: E712

    # Get projects for the first portfolio for charts
    first_portfolio_id = portfolios.iloc[0]["portfolio_id"] if not portfolios.empty else "pf-001"
    projects = get_portfolio_projects(first_portfolio_id, user_token=token)

    return html.Div([
        html.H4("Portfolios", className="page-title mb-3"),
        html.P(
            "Strategic portfolio overview with project health, budget burn, "
            "and value alignment.",
            className="page-subtitle mb-4",
        ),

        # KPI strip
        dbc.Row([
            dbc.Col(kpi_card("Portfolios", len(portfolios), "active portfolios"), width=3),
            dbc.Col(kpi_card("Total Projects", int(data["total_projects"]),
                             "across all portfolios"), width=3),
            dbc.Col(kpi_card("Total Budget", f"${data['total_budget']:,.0f}",
                             f"${data['total_spent']:,.0f} spent"), width=3),
            dbc.Col(kpi_card("Avg Completion", f"{data['avg_completion']:.0f}%",
                             "portfolio average"), width=3),
        ], className="kpi-strip mb-4"),

        # Charts row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Budget Burn by Project"),
                    dbc.CardBody(
                        dcc.Graph(
                            figure=budget_burn_chart(projects),
                            config={"displayModeBar": False},
                        ) if not projects.empty else empty_state("No project data.")
                    ),
                ], className="chart-card"),
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Strategic Alignment"),
                    dbc.CardBody(
                        dcc.Graph(
                            figure=strategic_bubble_chart(projects),
                            config={"displayModeBar": False},
                        ) if not projects.empty else empty_state("No project data.")
                    ),
                ], className="chart-card"),
            ], width=6),
        ], className="mb-4"),

        # Portfolio detail sections
        html.Div([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.Div([
                            html.Span(row["name"], className="fw-bold me-2"),
                            health_badge(row.get("health", "green")),
                        ], className="d-flex align-items-center"),
                        html.Div([
                            html.Small(
                                row.get("description", "") or "",
                                className="text-muted me-3",
                            ) if row.get("description") else html.Span(),
                            dbc.Button(
                                html.I(className="bi bi-pencil-square"),
                                id={"type": "portfolios-portfolio-edit-btn",
                                    "index": row["portfolio_id"]},
                                size="sm", color="link", className="p-0 me-2 text-muted",
                            ),
                            dbc.Button(
                                html.I(className="bi bi-trash"),
                                id={"type": "portfolios-portfolio-delete-btn",
                                    "index": row["portfolio_id"]},
                                size="sm", color="link", className="p-0 text-muted",
                            ),
                        ], className="d-flex align-items-center"),
                    ], className="d-flex justify-content-between align-items-center"),
                ]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Small("Owner", className="text-muted d-block"),
                            html.Span(row.get("owner", "N/A")),
                        ], width="auto", className="me-4"),
                        dbc.Col([
                            html.Small("Strategic Priority", className="text-muted d-block"),
                            html.Span(row.get("strategic_priority", "N/A") or "N/A"),
                        ], width="auto", className="me-4"),
                        dbc.Col([
                            html.Small("Projects", className="text-muted d-block"),
                            html.Span(str(int(row.get("project_count", 0) or 0))),
                        ], width="auto"),
                    ], className="mb-3"),
                    dbc.ListGroup([
                        _project_row(proj.to_dict())
                        for _, proj in get_portfolio_projects(
                            row["portfolio_id"], user_token=token
                        ).iterrows()
                    ]) if True else empty_state("No projects."),
                ]),
            ], className="mb-3")
            for _, row in portfolios.iterrows()
        ] if not portfolios.empty else [empty_state("No portfolios found.")]),
    ])


# -- Layout ----------------------------------------------------------


def layout():
    return html.Div([
        # Stores
        dcc.Store(id="portfolios-mutation-counter", data=0),
        dcc.Store(id="portfolios-selected-portfolio-store", data=None),

        # Toolbar
        dbc.Row([
            dbc.Col([], width=8),
            dbc.Col([
                dbc.Button(
                    [html.I(className="bi bi-plus-circle me-1"), "New Portfolio"],
                    id="portfolios-add-portfolio-btn", color="primary", size="sm",
                ),
            ], width=4, className="d-flex align-items-start justify-content-end"),
        ], className="mb-3"),

        # Content area
        html.Div(id="portfolios-content"),
        auto_refresh(interval_id="portfolios-refresh-interval"),

        # Modals
        crud_modal("portfolios-portfolio", "Create Portfolio", PORTFOLIO_FIELDS, size="lg"),
        confirm_delete_modal("portfolios-portfolio", "portfolio"),
    ])


# -- Callbacks -------------------------------------------------------


@callback(
    Output("portfolios-content", "children"),
    Input("portfolios-refresh-interval", "n_intervals"),
    Input("portfolios-mutation-counter", "data"),
    Input("active-department-store", "data"),
    Input("url", "search"),
)
def refresh_portfolios(n, mutation_count, dept_store, search):
    """Refresh portfolio content on interval, mutation, or department change."""
    # URL param takes priority, then store
    dept_id = get_param(search, "department_id") if search else None
    if not dept_id:
        dept_id = dept_store
    return _build_content(department_id=dept_id)


@callback(
    Output("portfolios-portfolio-modal", "is_open", allow_duplicate=True),
    Output("portfolios-portfolio-modal-title", "children", allow_duplicate=True),
    Output("portfolios-selected-portfolio-store", "data", allow_duplicate=True),
    Output("portfolios-portfolio-name", "value", allow_duplicate=True),
    Output("portfolios-portfolio-owner", "value", allow_duplicate=True),
    Output("portfolios-portfolio-description", "value", allow_duplicate=True),
    Output("portfolios-portfolio-strategic_priority", "value", allow_duplicate=True),
    Input("portfolios-add-portfolio-btn", "n_clicks"),
    Input({"type": "portfolios-portfolio-edit-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def toggle_portfolio_modal(add_clicks, edit_clicks):
    """Open portfolio modal for create (blank) or edit (populated)."""
    triggered = ctx.triggered_id

    # Create mode
    if triggered == "portfolios-add-portfolio-btn":
        return (True, "Create Portfolio", None, "", "", "", "")

    # Edit mode -- pattern-match button
    if isinstance(triggered, dict) and triggered.get("type") == "portfolios-portfolio-edit-btn":
        portfolio_id = triggered["index"]
        token = get_user_token()
        portfolio_df = get_portfolio(portfolio_id, user_token=token)
        if portfolio_df.empty:
            return (no_update,) * 7
        pf = portfolio_df.iloc[0]
        stored = {"portfolio_id": portfolio_id, "updated_at": str(pf.get("updated_at", ""))}
        return (
            True, f"Edit Portfolio -- {pf.get('name', portfolio_id)}",
            json.dumps(stored),
            pf.get("name", ""),
            pf.get("owner", ""),
            pf.get("description", ""),
            pf.get("strategic_priority", ""),
        )

    return (no_update,) * 7


@callback(
    Output("portfolios-portfolio-modal", "is_open", allow_duplicate=True),
    Output("portfolios-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    *modal_error_outputs("portfolios-portfolio", PORTFOLIO_FIELDS),
    Input("portfolios-portfolio-save-btn", "n_clicks"),
    State("portfolios-selected-portfolio-store", "data"),
    State("portfolios-mutation-counter", "data"),
    *modal_field_states("portfolios-portfolio", PORTFOLIO_FIELDS),
    prevent_initial_call=True,
)
def save_portfolio(n_clicks, stored_portfolio, counter, *field_values):
    """Save (create or update) a portfolio."""
    form_data = get_modal_values("portfolios-portfolio", PORTFOLIO_FIELDS, *field_values)

    token = get_user_token()
    email = get_user_email()

    if stored_portfolio:
        stored = json.loads(stored_portfolio) if isinstance(stored_portfolio, str) else stored_portfolio
        portfolio_id = stored["portfolio_id"]
        expected = stored.get("updated_at", "")
        result = update_portfolio_from_form(
            portfolio_id, form_data, expected,
            user_email=email, user_token=token,
        )
    else:
        result = create_portfolio_from_form(
            form_data, user_email=email, user_token=token,
        )

    if result["success"]:
        no_errors = set_field_errors("portfolios-portfolio", PORTFOLIO_FIELDS, {})
        error_outputs = []
        for inv, fb in zip(no_errors[0], no_errors[1]):
            error_outputs.extend([inv, fb])
        return (False, (counter or 0) + 1, result["message"], "Success", "success", True,
                *error_outputs)

    errors = result.get("errors", {})
    field_errors = set_field_errors("portfolios-portfolio", PORTFOLIO_FIELDS, errors)
    error_outputs = []
    for inv, fb in zip(field_errors[0], field_errors[1]):
        error_outputs.extend([inv, fb])
    return (True, no_update, result["message"], "Error", "danger", True,
            *error_outputs)


@callback(
    Output("portfolios-portfolio-delete-modal", "is_open", allow_duplicate=True),
    Output("portfolios-portfolio-delete-target-store", "data", allow_duplicate=True),
    Input({"type": "portfolios-portfolio-delete-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_delete_modal(n_clicks_list):
    """Open delete confirmation with the portfolio ID."""
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        return no_update, no_update
    portfolio_id = triggered["index"]
    return True, portfolio_id


@callback(
    Output("portfolios-portfolio-delete-modal", "is_open", allow_duplicate=True),
    Output("portfolios-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input("portfolios-portfolio-delete-confirm-btn", "n_clicks"),
    State("portfolios-portfolio-delete-target-store", "data"),
    State("portfolios-mutation-counter", "data"),
    prevent_initial_call=True,
)
def confirm_delete_portfolio(n_clicks, portfolio_id, counter):
    """Soft-delete the portfolio."""
    if not portfolio_id:
        return no_update, no_update, no_update, no_update, no_update, no_update

    token = get_user_token()
    email = get_user_email()
    success = delete_portfolio(portfolio_id, user_email=email, user_token=token)

    if success:
        return False, (counter or 0) + 1, "Portfolio deleted", "Deleted", "success", True
    return False, no_update, "Failed to delete portfolio", "Error", "danger", True


@callback(
    Output("portfolios-portfolio-modal", "is_open", allow_duplicate=True),
    Input("portfolios-portfolio-cancel-btn", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_portfolio_modal(n):
    """Close portfolio modal on cancel."""
    return False
