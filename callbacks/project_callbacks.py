"""Project Callbacks — populate and handle project selector."""

from dash import callback, Input, Output, no_update
from services.auth_service import get_user_token
from services.project_service import get_projects


@callback(
    Output("topbar-project-selector", "options"),
    Input("url", "pathname"),
    Input("active-department-store", "data"),
)
def populate_project_options(pathname, dept_id):
    """Load project options. Re-filters when department changes."""
    token = get_user_token()
    projects = get_projects(user_token=token)
    if projects.empty:
        return []

    # Filter by department if set (projects have department_id)
    if dept_id and "department_id" in projects.columns:
        projects = projects[projects["department_id"] == dept_id]

    # Filter out deleted
    if "is_deleted" in projects.columns:
        projects = projects[projects["is_deleted"] == False]  # noqa: E712

    return [
        {"label": row["name"], "value": row["project_id"]}
        for _, row in projects.iterrows()
    ]


@callback(
    Output("active-project-store", "data", allow_duplicate=True),
    Input("topbar-project-selector", "value"),
    prevent_initial_call=True,
)
def on_project_selected(project_id):
    """Update project store when dropdown changes."""
    return project_id
