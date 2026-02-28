"""Error Boundary — exception handling for page rendering and callbacks."""

import logging
import traceback
from functools import wraps
from dash import html
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)


def error_boundary(children, fallback_message="Something went wrong."):
    """Wrap already-built children — simple passthrough for backwards compatibility.

    Prefer safe_render() for actual error catching.
    """
    return children


def safe_render(render_fn, fallback_message="Unable to load this section."):
    """Safely execute a render function and catch any exceptions.

    Usage:
        def _build_charts():
            # might raise if data is bad
            return dcc.Graph(figure=some_chart(data))

        # In layout:
        safe_render(_build_charts, "Charts unavailable.")
    """
    try:
        return render_fn()
    except Exception as e:
        logger.error("Render error: %s\n%s", str(e), traceback.format_exc())
        return _error_card(fallback_message, str(e))


def safe_callback(fallback_message="An error occurred."):
    """Decorator for callbacks that catches exceptions and returns error UI.

    Usage:
        @callback(Output("my-output", "children"), Input("my-input", "n_intervals"))
        @safe_callback("Failed to refresh data.")
        def my_callback(n):
            # might raise
            return build_content()
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                logger.error(
                    "Callback error in %s: %s\n%s",
                    fn.__name__, str(e), traceback.format_exc(),
                )
                return _error_card(fallback_message, str(e))
        return wrapper
    return decorator


def _error_card(message, detail=None):
    """Render a user-friendly error card.

    In production, technical details are suppressed to prevent
    leaking SQL errors, file paths, or connection strings.
    """
    from config import get_settings

    children = [
        html.Div([
            html.I(className="bi bi-exclamation-triangle-fill me-2"),
            html.Span(message, className="fw-bold"),
        ], className="d-flex align-items-center mb-2"),
    ]
    if detail and not get_settings().is_production:
        children.append(
            html.Details([
                html.Summary("Technical Details", className="text-muted small"),
                html.Pre(
                    str(detail)[:500],
                    className="small mt-2 p-2 bg-dark rounded",
                    style={"whiteSpace": "pre-wrap", "fontSize": "0.75rem"},
                ),
            ])
        )
    return dbc.Alert(
        children,
        color="danger",
        className="m-2",
        dismissable=True,
    )
