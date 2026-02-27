"""Navigation Callbacks — breadcrumb and sidebar state."""

from dash import callback, Input, Output, html, dcc
from utils.url_state import get_param


@callback(
    Output("page-breadcrumb", "children"),
    Input("url", "pathname"),
    Input("url", "search"),
)
def update_breadcrumb(pathname, search):
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
    crumbs = [
        dcc.Link("PM Hub", href="/", className="breadcrumb-root",
                 style={"textDecoration": "none", "color": "inherit"}),
    ]

    # Add context-aware segments
    dept_id = get_param(search, "department_id") if search else None
    portfolio_id = get_param(search, "portfolio_id") if search else None

    if dept_id and pathname == "/portfolios":
        crumbs.append(html.Span(" / ", className="breadcrumb-sep"))
        crumbs.append(dcc.Link(
            "Dashboard", href="/", className="breadcrumb-link",
            style={"textDecoration": "none", "color": "inherit"},
        ))

    if portfolio_id and pathname == "/projects":
        crumbs.append(html.Span(" / ", className="breadcrumb-sep"))
        crumbs.append(dcc.Link(
            "Portfolios", href="/portfolios", className="breadcrumb-link",
            style={"textDecoration": "none", "color": "inherit"},
        ))

    crumbs.append(html.Span(" / ", className="breadcrumb-sep"))
    crumbs.append(html.Span(name, className="breadcrumb-current"))

    return crumbs
