"""Error Boundary — wraps sections for independent failure handling."""

from dash import html
import dash_bootstrap_components as dbc


def error_boundary(children, fallback_message="Something went wrong."):
    try:
        return children
    except Exception:
        return dbc.Alert(fallback_message, color="danger", className="m-2")
