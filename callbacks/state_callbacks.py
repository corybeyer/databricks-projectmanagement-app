"""State Callbacks — manage application-wide dcc.Store state."""

from dash import callback, Input, Output, State, no_update
from services.auth_service import get_current_user
from utils.url_state import get_param


@callback(
    Output("user-context-store", "data"),
    Input("url", "pathname"),
    State("user-context-store", "data"),
)
def init_user_context(pathname, current_data):
    """Initialize user context on first page load."""
    if current_data is not None:
        return no_update
    user = get_current_user()
    return {
        "email": user["email"],
        "display_name": user["email"].split("@")[0] if user["email"] else "User",
    }


@callback(
    Output("active-department-store", "data"),
    Input("url", "search"),
    State("active-department-store", "data"),
)
def update_department_from_url(search, current):
    """Update department context from URL query params."""
    dept_id = get_param(search, "department_id")
    if dept_id:
        return dept_id
    return no_update


@callback(
    Output("active-portfolio-store", "data"),
    Input("url", "search"),
    State("active-portfolio-store", "data"),
)
def update_portfolio_from_url(search, current):
    """Update portfolio context from URL query params."""
    portfolio_id = get_param(search, "portfolio_id")
    if portfolio_id:
        return portfolio_id
    return no_update


@callback(
    Output("active-project-store", "data"),
    Input("url", "search"),
    State("active-project-store", "data"),
)
def update_project_from_url(search, current):
    """Update project context from URL query params."""
    project_id = get_param(search, "project_id")
    if project_id:
        return project_id
    return no_update


@callback(
    Output("active-sprint-store", "data"),
    Input("url", "search"),
    State("active-sprint-store", "data"),
)
def update_sprint_from_url(search, current):
    """Update sprint context from URL query params."""
    sprint_id = get_param(search, "sprint_id")
    if sprint_id:
        return sprint_id
    return no_update
