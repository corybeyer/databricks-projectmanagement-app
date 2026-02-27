"""Department Selector — topbar dropdown for department context."""

from dash import dcc, html
import dash_bootstrap_components as dbc


def department_selector():
    """Return the department dropdown for the topbar.

    Options are populated via callback in callbacks/department_callbacks.py.
    """
    return html.Div([
        html.Small("Department", className="text-muted me-2",
                   style={"whiteSpace": "nowrap"}),
        dcc.Dropdown(
            id="topbar-dept-selector",
            placeholder="All Departments",
            clearable=True,
            style={"minWidth": "180px"},
            className="topbar-dropdown",
        ),
    ], className="d-flex align-items-center me-3")
