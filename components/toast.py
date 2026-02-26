"""
Toast Notification Component
==============================
Reusable toast/alert system for user feedback.

Usage in callbacks:
    Output("toast-store", "data")
    return {"message": "Task created", "type": "success", "header": "Success"}

Supported types: "success", "error", "warning", "info"
"""

from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Output


def toast_container():
    """Return a positioned toast container for the app layout.

    Place this once in app.py layout. Callbacks update the toast
    via the ``toast-store`` dcc.Store component.
    """
    return html.Div(
        dbc.Toast(
            id="toast-message",
            header="Notification",
            is_open=False,
            dismissable=True,
            duration=4000,
            icon="info",
            style={"position": "fixed", "top": 16, "right": 16, "zIndex": 9999},
        ),
        id="toast-container",
    )


def make_toast_output():
    """Return the list of Output targets that callbacks need to update the toast.

    Usage::

        @app.callback(
            *make_toast_output(),
            ...
        )
        def my_callback(...):
            ...
            return "Task saved", "Success", "success", True
    """
    return [
        Output("toast-message", "children"),
        Output("toast-message", "header"),
        Output("toast-message", "icon"),
        Output("toast-message", "is_open"),
    ]
