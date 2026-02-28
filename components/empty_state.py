"""Empty State — placeholder when no data is available."""

from dash import html


def empty_state(message="No data available.", icon=None):
    children = []
    if icon:
        children.append(
            html.Div(html.I(className=f"bi bi-{icon}"), className="empty-state-icon")
        )
    children.append(html.Div(message))
    return html.Div(children, className="empty-state")
