"""Department Callbacks — populate and handle department selector."""

from dash import callback, Input, Output, State, no_update
from services.auth_service import get_user_token
from services.department_service import get_departments


@callback(
    Output("topbar-dept-selector", "options"),
    Input("url", "pathname"),
)
def populate_department_options(pathname):
    """Load department options on any page navigation."""
    token = get_user_token()
    depts = get_departments(user_token=token)
    if depts.empty:
        return []
    return [
        {"label": row["name"], "value": row["department_id"]}
        for _, row in depts.iterrows()
    ]


@callback(
    Output("active-department-store", "data", allow_duplicate=True),
    Input("topbar-dept-selector", "value"),
    prevent_initial_call=True,
)
def on_department_selected(dept_id):
    """Update department store when dropdown changes."""
    return dept_id
