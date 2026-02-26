"""Navigation Callbacks — breadcrumb and sidebar state."""

from dash import callback, Input, Output, html


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
