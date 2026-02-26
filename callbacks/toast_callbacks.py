"""
Toast Callbacks
================
Listens on ``toast-store`` (dcc.Store) and opens the toast notification
with the appropriate color and message.

Expected store data format::

    {"message": "...", "type": "success|error|warning|info", "header": "..."}
"""

from dash import Input, Output, callback, no_update

# Map user-friendly type names to dbc.Toast icon colors
_TYPE_MAP = {
    "success": "success",
    "error": "danger",
    "danger": "danger",
    "warning": "warning",
    "info": "primary",
}


@callback(
    Output("toast-message", "children"),
    Output("toast-message", "header"),
    Output("toast-message", "icon"),
    Output("toast-message", "is_open"),
    Input("toast-store", "data"),
    prevent_initial_call=True,
)
def _show_toast(data):
    """Open toast when toast-store receives new data."""
    if not data:
        return no_update, no_update, no_update, no_update

    message = data.get("message", "")
    header = data.get("header", "Notification")
    toast_type = data.get("type", "info")
    icon = _TYPE_MAP.get(toast_type, "primary")

    return message, header, icon, True
