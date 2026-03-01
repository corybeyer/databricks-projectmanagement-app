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
from config.logging import setup_logging, set_trace_id, clear_trace_id
from components.app_state import app_stores
from components.toast import toast_container
from components.department_selector import department_selector
from components.project_selector import project_selector
from components.notification_bell import notification_bell
from components.error_boundary import log_callback

# ─── Init ──────────────────────────────────────────────────
settings = get_settings()
setup_logging(level=settings.log_level)

# ─── Monkey-patch dash.callback to auto-instrument all callbacks ──
_original_callback = dash.callback


def _instrumented_callback(*args, **kwargs):
    """Wrap every dash.callback so it automatically gets logging."""
    original_decorator = _original_callback(*args, **kwargs)

    def wrapper(fn):
        instrumented_fn = log_callback()(fn)
        return original_decorator(instrumented_fn)
    return wrapper


dash.callback = _instrumented_callback

app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    title="PM Hub — Portfolio & Project Management",
)
server = app.server  # Required for Databricks Apps deployment


# ─── Trace ID hooks ──────────────────────────────────────────
@server.before_request
def _set_trace_id():
    """Generate a trace ID for each Flask request."""
    set_trace_id()


@server.teardown_request
def _clear_trace_id(exc=None):
    """Clear trace ID after request completes."""
    clear_trace_id()


# Register callbacks
import callbacks  # noqa: F401, E402


# ─── Navbar Helpers ────────────────────────────────────────
def make_dropdown_item(label, href, icon):
    return dbc.DropdownMenuItem(
        [html.I(className=f"bi bi-{icon} me-2"), label],
        href=href,
        className="navbar-dropdown-item",
    )


# ─── Horizontal Navbar ────────────────────────────────────
navbar = dbc.Navbar(
    dbc.Container(
        [
            # Brand
            html.A(
                html.Div(
                    [
                        html.Div("PM", className="navbar-logo"),
                        html.Span("PM Hub", className="navbar-brand-text"),
                    ],
                    className="d-flex align-items-center",
                ),
                href="/",
                className="text-decoration-none",
            ),
            # Mobile toggler
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            # Collapsible content
            dbc.Collapse(
                dbc.Nav(
                    [
                        # ── Portfolio dropdown ──
                        dbc.DropdownMenu(
                            [
                                make_dropdown_item("Dashboard", "/", "grid-1x2-fill"),
                                make_dropdown_item("Portfolios", "/portfolios", "collection-fill"),
                                make_dropdown_item("Roadmap", "/roadmap", "calendar-range-fill"),
                            ],
                            label="Portfolio",
                            nav=True,
                            in_navbar=True,
                            className="navbar-section-dropdown",
                        ),
                        # ── Projects dropdown ──
                        dbc.DropdownMenu(
                            [
                                make_dropdown_item("All Projects", "/projects", "kanban-fill"),
                                make_dropdown_item("Project Charters", "/charters", "file-earmark-text-fill"),
                                make_dropdown_item("Gantt Timeline", "/gantt", "bar-chart-steps"),
                                make_dropdown_item("Sprint Board", "/sprint", "view-stacked"),
                            ],
                            label="Projects",
                            nav=True,
                            in_navbar=True,
                            className="navbar-section-dropdown",
                        ),
                        # ── Execution dropdown ──
                        dbc.DropdownMenu(
                            [
                                make_dropdown_item("My Work", "/my-work", "person-check-fill"),
                                make_dropdown_item("Backlog", "/backlog", "list-check"),
                                make_dropdown_item("Retrospectives", "/retros", "arrow-repeat"),
                                make_dropdown_item("Comments", "/comments", "chat-dots"),
                                make_dropdown_item("Timesheet", "/timesheet", "clock-history"),
                            ],
                            label="Execution",
                            nav=True,
                            in_navbar=True,
                            className="navbar-section-dropdown",
                        ),
                        # ── Governance direct link ──
                        dbc.NavItem(
                            dbc.NavLink(
                                "Governance",
                                href="/deliverables",
                                className="navbar-direct-link",
                            ),
                        ),
                        # ── Analytics dropdown ──
                        dbc.DropdownMenu(
                            [
                                make_dropdown_item("Reports", "/reports", "graph-up-arrow"),
                                make_dropdown_item("Resource Allocation", "/resources", "people-fill"),
                                make_dropdown_item("Risk Register", "/risks", "shield-exclamation"),
                            ],
                            label="Analytics",
                            nav=True,
                            in_navbar=True,
                            className="navbar-section-dropdown",
                        ),
                    ],
                    className="me-auto",
                    navbar=True,
                ),
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),
            # ── Right-side controls ──
            html.Div(
                [
                    html.Div(id="page-breadcrumb", className="navbar-breadcrumb"),
                    department_selector(),
                    project_selector(),
                    notification_bell(),
                    html.Span("FY2026 Q1", className="navbar-period"),
                    html.Span("●", className="navbar-status-dot"),
                    html.Span("Live", className="navbar-status"),
                ],
                className="navbar-right-controls",
            ),
        ],
        fluid=True,
    ),
    className="navbar-glass",
    dark=True,
    expand="lg",
)

# ─── Main Layout ────────────────────────────────────────────
app.layout = html.Div(
    [
        dcc.Location(id="url"),
        *app_stores(),
        toast_container(),
        navbar,
        html.Div(
            dash.page_container,
            className="page-content",
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
