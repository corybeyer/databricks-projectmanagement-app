"""Project Selector — topbar dropdown for project context."""

from dash import dcc, html


def project_selector():
    """Return the project dropdown for the topbar.

    Options are populated via callback in callbacks/project_callbacks.py.
    """
    return html.Div([
        html.Small("Project", className="text-muted me-2",
                   style={"whiteSpace": "nowrap"}),
        dcc.Dropdown(
            id="topbar-project-selector",
            placeholder="All Projects",
            clearable=True,
            style={"minWidth": "200px"},
            className="topbar-dropdown",
        ),
    ], className="d-flex align-items-center me-3")
