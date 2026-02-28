"""
Databricks PM App — Portfolio & Project Management
====================================================
Dash (Plotly) application deployed via Databricks Apps.
Supports: Portfolio Management, Hybrid Waterfall/Agile,
Project Charters, Sprint Boards, Gantt Timelines, Reporting.

Run locally:  python app.py
Deploy:       databricks apps deploy pm-app --source-code-path ./databricks-pm-app
"""

import os
import signal
import sys
import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from config import get_settings
from config.logging import setup_logging
from components.app_state import app_stores
from components.toast import toast_container
from components.department_selector import department_selector
from components.project_selector import project_selector
from components.notification_bell import notification_bell

# ─── Init ──────────────────────────────────────────────────
setup_logging()
settings = get_settings()

app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    title="PM Hub — Portfolio & Project Management",
)
server = app.server  # Required for Databricks Apps deployment

# Register callbacks
import callbacks  # noqa: F401, E402

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
        html.Div(
            [
                html.Div("PM", className="sidebar-logo"),
                html.Div("PM Hub", className="sidebar-brand"),
            ],
            className="sidebar-header",
        ),
        html.Hr(className="sidebar-divider"),

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
        make_nav_link("Comments", "/comments", "chat-dots"),
        make_nav_link("Timesheet", "/timesheet", "clock-history"),

        html.Div("PMI GOVERNANCE", className="sidebar-section-label mt-3"),
        make_nav_link("Deliverables", "/deliverables", "box-seam-fill"),

        html.Div("ANALYTICS", className="sidebar-section-label mt-3"),
        make_nav_link("Reports", "/reports", "graph-up-arrow"),
        make_nav_link("Resource Allocation", "/resources", "people-fill"),
        make_nav_link("Risk Register", "/risks", "shield-exclamation"),

        html.Div(
            [
                html.Div("Unity Catalog", className="sidebar-footer-item"),
                html.Div(f"{settings.uc_catalog}.{settings.uc_schema}", className="sidebar-footer-schema"),
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
        *app_stores(),
        toast_container(),
        sidebar,
        html.Div(
            [
                html.Div(
                    [
                        html.Div(id="page-breadcrumb", className="topbar-breadcrumb"),
                        html.Div(
                            [
                                department_selector(),
                                project_selector(),
                                notification_bell(),
                                html.Span("FY2026 Q1", className="topbar-period"),
                                html.Span("●", className="topbar-status-dot"),
                                html.Span("Live", className="topbar-status"),
                            ],
                            className="topbar-right",
                        ),
                    ],
                    className="topbar",
                ),
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


# ─── Graceful Shutdown ──────────────────────────────────────
def _handle_sigterm(signum, frame):
    """Handle SIGTERM from Databricks Apps for graceful shutdown."""
    sys.exit(0)

signal.signal(signal.SIGTERM, _handle_sigterm)


# ─── Entry Point ────────────────────────────────────────────
if __name__ == "__main__":
    if settings.is_production and settings.debug:
        raise RuntimeError("Debug mode must not be enabled in production")
    port = int(os.getenv("DATABRICKS_APP_PORT", settings.app_port))
    app.run(debug=settings.debug, host="0.0.0.0", port=port)
