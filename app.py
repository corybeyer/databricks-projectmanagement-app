"""
Databricks PM App — Portfolio & Project Management
====================================================
Dash (Plotly) application deployed via Databricks Apps.
Supports: Portfolio Management, Hybrid Waterfall/Agile, 
Project Charters, Sprint Boards, Gantt Timelines, Reporting.

Run locally:  python app.py
Deploy:       databricks apps deploy pm-app --source-code-path ./databricks-pm-app
"""

import dash
from dash import Dash, html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc

# ─── App Init ───────────────────────────────────────────────
app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.SLATE],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    title="PM Hub — Portfolio & Project Management",
)
server = app.server  # Required for Databricks Apps deployment

# ─── Sidebar Navigation ────────────────────────────────────
def make_nav_link(label, href, icon):
    return dbc.NavLink(
        [html.I(className=f"bi bi-{icon} me-2"), label],
        href=href,
        active="exact",
        className="sidebar-link",
    )

sidebar = html.Div(
    [
        # Logo / Brand
        html.Div(
            [
                html.Div("PM", className="sidebar-logo"),
                html.Div("PM Hub", className="sidebar-brand"),
            ],
            className="sidebar-header",
        ),
        html.Hr(className="sidebar-divider"),

        # Navigation sections
        html.Div("PORTFOLIO", className="sidebar-section-label"),
        make_nav_link("Dashboard", "/", "grid-1x2-fill"),
        make_nav_link("Portfolios", "/portfolios", "collection-fill"),
        make_nav_link("Roadmap", "/roadmap", "calendar-range-fill"),

        html.Div("PROJECTS", className="sidebar-section-label mt-3"),
        make_nav_link("All Projects", "/projects", "kanban-fill"),
        make_nav_link("Project Charters", "/charters", "file-earmark-text-fill"),
        make_nav_link("Gantt Timeline", "/gantt", "bar-chart-steps"),
        make_nav_link("Sprint Board", "/sprint", "view-stacked"),

        html.Div("EXECUTION", className="sidebar-section-label mt-3"),
        make_nav_link("My Work", "/my-work", "person-check-fill"),
        make_nav_link("Backlog", "/backlog", "list-check"),
        make_nav_link("Retrospectives", "/retros", "arrow-repeat"),

        html.Div("ANALYTICS", className="sidebar-section-label mt-3"),
        make_nav_link("Reports", "/reports", "graph-up-arrow"),
        make_nav_link("Resource Allocation", "/resources", "people-fill"),
        make_nav_link("Risk Register", "/risks", "shield-exclamation"),

        # Footer
        html.Div(
            [
                html.Div("Unity Catalog", className="sidebar-footer-item"),
                html.Div("workspace.project_management", className="sidebar-footer-schema"),
            ],
            className="sidebar-footer",
        ),
    ],
    className="sidebar",
)

# ─── Main Layout ────────────────────────────────────────────
app.layout = html.Div(
    [
        dcc.Location(id="url"),
        sidebar,
        html.Div(
            [
                # Top bar
                html.Div(
                    [
                        html.Div(id="page-breadcrumb", className="topbar-breadcrumb"),
                        html.Div(
                            [
                                html.Span("FY2026 Q1", className="topbar-period"),
                                html.Span("●", className="topbar-status-dot"),
                                html.Span("Live", className="topbar-status"),
                            ],
                            className="topbar-right",
                        ),
                    ],
                    className="topbar",
                ),
                # Page content
                html.Div(
                    dash.page_container,
                    className="page-content",
                ),
            ],
            className="main-content",
        ),
    ],
    className="app-container",
)


# ─── Breadcrumb callback ────────────────────────────────────
@callback(
    Output("page-breadcrumb", "children"),
    Input("url", "pathname"),
)
def update_breadcrumb(pathname):
    page_names = {
        "/": "Portfolio Dashboard",
        "/portfolios": "Portfolios",
        "/roadmap": "Roadmap Timeline",
        "/projects": "All Projects",
        "/charters": "Project Charters",
        "/gantt": "Gantt Timeline",
        "/sprint": "Sprint Board",
        "/my-work": "My Work",
        "/backlog": "Backlog",
        "/retros": "Retrospectives",
        "/reports": "Reports",
        "/resources": "Resource Allocation",
        "/risks": "Risk Register",
    }
    name = page_names.get(pathname, "Page")
    return [
        html.Span("PM Hub", className="breadcrumb-root"),
        html.Span(" / ", className="breadcrumb-sep"),
        html.Span(name, className="breadcrumb-current"),
    ]


# ─── Entry Point ────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
