"""Empty State — placeholder when no data is available."""

from dash import html


def empty_state(message="No data available."):
    return html.Div(message, className="text-muted p-4 text-center")
