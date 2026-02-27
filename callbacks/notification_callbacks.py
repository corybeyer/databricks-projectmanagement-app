"""Notification callbacks — bell badge, dropdown, mark-read."""

from dash import callback, Output, Input, State, no_update, html
import dash_bootstrap_components as dbc
from services import notification_service
from services.auth_service import get_current_user


@callback(
    Output("notification-badge", "children"),
    Output("notification-badge", "style"),
    Input("notification-refresh-interval", "n_intervals"),
    prevent_initial_call=False,
)
def update_badge(n_intervals):
    """Update the notification badge count every 30s."""
    user = get_current_user()
    count = notification_service.get_unread_count(user["email"])
    if count > 0:
        return str(count) if count < 100 else "99+", {"display": "inline"}
    return "", {"display": "none"}


@callback(
    Output("notification-dropdown", "children"),
    Input("notification-dropdown", "is_open"),
    prevent_initial_call=True,
)
def load_notifications(is_open):
    """Load notifications when dropdown opens."""
    if not is_open:
        return no_update

    user = get_current_user()
    notifications = notification_service.get_all(user["email"])

    if not notifications:
        items = [
            dbc.DropdownMenuItem(
                "No notifications",
                disabled=True,
                className="text-muted",
            )
        ]
    else:
        items = []
        for notif in notifications[:10]:
            is_unread = not notif.get("is_read", True)
            items.append(
                dbc.DropdownMenuItem(
                    [
                        html.Div(
                            [
                                html.Strong(notif.get("title", "")),
                                html.Span(
                                    " \u25cf" if is_unread else "",
                                    className="text-primary ms-1",
                                ),
                            ]
                        ),
                        html.Small(
                            notif.get("message", ""),
                            className="text-muted d-block",
                        ),
                    ],
                    className="py-2" + (" fw-bold" if is_unread else ""),
                )
            )

    items.append(dbc.DropdownMenuItem(divider=True))
    items.append(
        dbc.DropdownMenuItem(
            "Mark all as read",
            id="notification-mark-all-read",
        )
    )
    return items


@callback(
    Output("notification-store", "data"),
    Input("notification-mark-all-read", "n_clicks"),
    prevent_initial_call=True,
)
def mark_all_read(n_clicks):
    """Mark all notifications as read."""
    if not n_clicks:
        return no_update
    user = get_current_user()
    notification_service.mark_all_read(user["email"])
    return {"action": "marked_all_read"}
