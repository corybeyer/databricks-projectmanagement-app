"""
All Projects Page
==================
Project list with health badges, progress bars, and key metrics.
"""

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
from services.auth_service import get_user_token
from services.portfolio_service import get_portfolio_projects
from components.health_badge import health_badge
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from charts.theme import COLORS

dash.register_page(__name__, path="/projects", name="All Projects")


def _project_card(project):
    """Render a project summary card."""
    pct = project.get("pct_complete", 0)
    budget_pct = (
        project.get("budget_spent", 0) / max(project.get("budget_total", 1), 1) * 100
    )
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
                        project.get("delivery_method", "N/A").title(),
                        className="badge bg-secondary",
                    ),
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
                html.Small(
                    f"${project.get('budget_spent', 0):,.0f} / "
                    f"${project.get('budget_total', 0):,.0f}",
                    className="text-muted",
                ),
            ]),
        ], className="project-card h-100"),
    ], width=4, className="mb-3")


def _build_content():
    """Build the actual page content."""
    token = get_user_token()
    projects = get_portfolio_projects("pf-001", user_token=token)

    return html.Div([
        html.H4("All Projects", className="page-title mb-3"),
        html.P(
            "Overview of all active projects across portfolios with status, "
            "health, and budget tracking.",
            className="page-subtitle mb-4",
        ),

        # Summary stats
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Span(str(len(projects)), className="fs-4 fw-bold me-2"),
                    html.Span("projects", className="text-muted"),
                ]),
            ], width="auto"),
            dbc.Col([
                html.Div([
                    html.Span("● ", style={"color": COLORS["green"]}),
                    html.Span(
                        f"{len(projects[projects['health'] == 'green'])} on track",
                        className="text-muted me-3",
                    ),
                    html.Span("● ", style={"color": COLORS["yellow"]}),
                    html.Span(
                        f"{len(projects[projects['health'] == 'yellow'])} at risk",
                        className="text-muted me-3",
                    ),
                    html.Span("● ", style={"color": COLORS["red"]}),
                    html.Span(
                        f"{len(projects[projects['health'] == 'red'])} off track",
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
            dbc.Col(empty_state("No projects found."), width=12),
        ]),
    ])


def layout():
    return html.Div([
        html.Div(id="projects-content"),
        auto_refresh(interval_id="projects-refresh-interval"),
    ])


@callback(
    Output("projects-content", "children"),
    Input("projects-refresh-interval", "n_intervals"),
)
def refresh_projects(n):
    return _build_content()
