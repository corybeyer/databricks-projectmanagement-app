"""Change History — reusable component showing entity change log."""

from dash import html
import dash_bootstrap_components as dbc


def change_history_panel(history_records, entity_label="Item"):
    """Render a change history panel for an entity.

    Args:
        history_records: List of dicts from change_history_service.get_history()
        entity_label: Display name (e.g., "Task", "Risk")

    Returns:
        Dash component showing the change timeline
    """
    if not history_records:
        return html.Div(
            html.Small("No change history available.", className="text-muted"),
            className="p-3",
        )

    items = []
    for record in history_records[:20]:  # Limit to 20 most recent
        items.append(_history_item(record))

    return html.Div([
        html.H6(f"{entity_label} History", className="mb-3"),
        html.Div(items, className="change-history-timeline"),
    ])


def last_modified_footer(updated_by=None, updated_at=None):
    """Render a 'Last modified by [user] at [time]' footer for edit modals.

    Args:
        updated_by: User email who last modified
        updated_at: Timestamp of last modification

    Returns:
        Dash component for modal footer
    """
    if not updated_by and not updated_at:
        return html.Div()

    parts = []
    if updated_by:
        display_name = (
            updated_by.split("@")[0] if "@" in str(updated_by)
            else str(updated_by)
        )
        parts.append(f"Last modified by {display_name}")
    if updated_at:
        parts.append(f"at {str(updated_at)[:19]}")

    return html.Div(
        html.Small(" ".join(parts), className="text-muted"),
        className="mt-2 pt-2 border-top border-secondary",
    )


def _history_item(record):
    """Render a single history entry."""
    action = record.get("action", "update")
    user = record.get("user_email", "Unknown")
    display_name = (
        user.split("@")[0] if "@" in str(user) else str(user)
    )
    timestamp = str(record.get("created_at", ""))[:19]
    field = record.get("field_changed")
    old_val = record.get("old_value")
    new_val = record.get("new_value")
    details = record.get("details")

    # Action badge colors
    action_colors = {
        "create": "success", "update": "primary", "delete": "danger",
        "approve": "success", "reject": "danger",
    }

    content = [
        html.Div([
            dbc.Badge(
                action.title(),
                color=action_colors.get(action, "secondary"),
                className="me-2",
            ),
            html.Small(display_name, className="fw-bold me-2"),
            html.Small(timestamp, className="text-muted"),
        ], className="d-flex align-items-center"),
    ]

    if field:
        change_text = f"Changed {field}"
        if old_val and new_val:
            change_text += f": {_truncate(old_val)} \u2192 {_truncate(new_val)}"
        elif new_val:
            change_text += f": \u2192 {_truncate(new_val)}"
        content.append(
            html.Small(change_text, className="text-muted d-block mt-1")
        )
    elif details:
        content.append(
            html.Small(details, className="text-muted d-block mt-1")
        )

    return html.Div(content, className="mb-3 pb-2 border-bottom border-secondary")


def _truncate(value, max_len=50):
    """Truncate a string value for display."""
    s = str(value)
    return s if len(s) <= max_len else s[:max_len] + "..."
