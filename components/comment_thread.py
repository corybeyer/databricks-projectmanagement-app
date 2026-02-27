"""
Comment Thread Component — reusable comment display and input.

Renders a list of comments for a given task with author, body,
timestamp, and edit/delete buttons for the current user's own comments.
Also includes an "Add Comment" textarea and submit button.
"""

from dash import html
import dash_bootstrap_components as dbc
import pandas as pd


def comment_thread(task_id: str, id_prefix: str, current_user: str = None) -> html.Div:
    """Return a comment thread container.

    The actual comment list is populated by a callback (via the
    ``{id_prefix}-comment-list`` div). This function builds the
    static shell: the list container and the add-comment form.

    Args:
        task_id: The task ID this thread is for.
        id_prefix: Prefix for all component IDs.
        current_user: Email of the currently logged-in user.

    Returns:
        An ``html.Div`` containing the thread structure.
    """
    return html.Div([
        # Comment list — populated by callback
        html.Div(id=f"{id_prefix}-comment-list", className="mb-3"),

        # Add comment form
        html.Hr(className="my-3"),
        html.Div([
            dbc.Label("Add a Comment", className="fw-bold small mb-1"),
            dbc.Textarea(
                id=f"{id_prefix}-comment-input",
                placeholder="Write your comment here...",
                rows=3,
                className="mb-2",
            ),
            dbc.FormFeedback(
                id=f"{id_prefix}-comment-input-feedback",
                type="invalid",
            ),
            html.Div([
                dbc.Button(
                    [html.I(className="bi bi-chat-dots me-1"), "Post Comment"],
                    id=f"{id_prefix}-comment-submit",
                    color="primary",
                    size="sm",
                ),
            ], className="d-flex justify-content-end"),
        ]),
    ], className="comment-thread")


def comment_card(comment_row, id_prefix: str, current_user: str = None) -> dbc.Card:
    """Render a single comment as a card.

    Args:
        comment_row: A dict or Series with comment fields
            (comment_id, author, body, created_at, updated_at).
        id_prefix: Prefix for component IDs.
        current_user: Email of the currently logged-in user, used to
            show edit/delete buttons on own comments.

    Returns:
        A ``dbc.Card`` displaying the comment.
    """
    if isinstance(comment_row, pd.Series):
        comment_row = comment_row.to_dict()

    comment_id = comment_row.get("comment_id", "")
    author = comment_row.get("author", "Unknown")
    body = comment_row.get("body", "")
    created_at = str(comment_row.get("created_at", ""))

    # Format timestamp
    if created_at and len(created_at) >= 16:
        display_time = created_at[:16]
    elif created_at:
        display_time = created_at
    else:
        display_time = "Unknown time"

    # Show edit/delete only for own comments
    is_own = current_user and author and current_user.lower() == author.lower()
    action_buttons = []
    if is_own:
        action_buttons = [
            dbc.Button(
                html.I(className="bi bi-pencil-square"),
                id={"type": f"{id_prefix}-comment-edit-btn", "index": comment_id},
                size="sm", color="link", className="p-0 me-2 text-muted",
                title="Edit comment",
            ),
            dbc.Button(
                html.I(className="bi bi-trash"),
                id={"type": f"{id_prefix}-comment-delete-btn", "index": comment_id},
                size="sm", color="link", className="p-0 text-muted",
                title="Delete comment",
            ),
        ]

    # Author initial for avatar
    initial = author[0].upper() if author else "?"

    return dbc.Card([
        dbc.CardBody([
            html.Div([
                # Avatar + author info
                html.Div([
                    html.Div(
                        initial,
                        className="comment-avatar",
                        style={
                            "width": "32px", "height": "32px",
                            "borderRadius": "50%",
                            "backgroundColor": "#495057",
                            "color": "#adb5bd",
                            "display": "flex", "alignItems": "center",
                            "justifyContent": "center",
                            "fontSize": "0.8rem", "fontWeight": "bold",
                            "flexShrink": "0",
                        },
                    ),
                    html.Div([
                        html.Span(author, className="fw-bold small"),
                        html.Span(
                            f" \u00b7 {display_time}",
                            className="text-muted small ms-1",
                        ),
                    ], className="ms-2"),
                ], className="d-flex align-items-center"),

                # Action buttons
                html.Div(action_buttons, className="d-flex align-items-center")
                if action_buttons else html.Div(),
            ], className="d-flex justify-content-between align-items-start mb-2"),

            # Comment body
            html.P(body, className="mb-0 small", style={"whiteSpace": "pre-wrap"}),
        ], className="py-2 px-3"),
    ], className="mb-2", style={"backgroundColor": "#2b3035", "border": "1px solid #3a4047"})


def comment_list_display(comments_df: pd.DataFrame, id_prefix: str,
                         current_user: str = None) -> html.Div:
    """Render a list of comments from a DataFrame.

    Args:
        comments_df: DataFrame of comments.
        id_prefix: Prefix for component IDs.
        current_user: Email of the currently logged-in user.

    Returns:
        An ``html.Div`` containing rendered comment cards or an empty-state message.
    """
    if comments_df is None or comments_df.empty:
        return html.Div(
            html.P("No comments yet. Be the first to comment.",
                   className="text-muted text-center py-3"),
        )

    cards = []
    for _, row in comments_df.iterrows():
        cards.append(comment_card(row, id_prefix, current_user=current_user))

    return html.Div(cards)
