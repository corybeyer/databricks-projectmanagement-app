"""Notification Bell — topbar notification indicator."""

from dash import html, dcc
import dash_bootstrap_components as dbc


def notification_bell():
    """Notification bell with unread count badge and dropdown panel."""
    return html.Div(
        [
            dcc.Store(id="notification-store", storage_type="memory"),
            dcc.Interval(id="notification-refresh-interval", interval=30_000),
            dbc.DropdownMenu(
                label=[
                    html.I(className="bi bi-bell-fill"),
                    dbc.Badge(
                        id="notification-badge",
                        color="danger",
                        pill=True,
                        className="position-absolute top-0 start-100 translate-middle",
                        style={"display": "none"},
                    ),
                ],
                id="notification-dropdown",
                children=[
                    dbc.DropdownMenuItem(
                        "Loading notifications...",
                        id="notification-list-placeholder",
                        disabled=True,
                    ),
                    dbc.DropdownMenuItem(divider=True),
                    dbc.DropdownMenuItem(
                        "Mark all as read",
                        id="notification-mark-all-read",
                    ),
                ],
                direction="down",
                align_end=True,
                toggle_class_name="btn btn-link text-light position-relative p-1",
                className="notification-bell",
            ),
        ],
        className="d-inline-block",
    )
