"""Error Boundary — exception handling for page rendering and callbacks."""

import logging
import time
import traceback
from functools import wraps
from dash import html, ctx
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


def log_callback():
    """Logging-only decorator for callbacks. Logs name, trigger, duration, errors.

    Unlike safe_callback(), this re-raises exceptions so Dash handles them
    normally. Used by the auto-instrument monkey-patch in app.py.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            trigger = _get_trigger()
            start = time.monotonic()
            try:
                result = fn(*args, **kwargs)
                duration_ms = (time.monotonic() - start) * 1000
                if duration_ms > 50:
                    logger.info(
                        "Callback %s [trigger=%s] completed in %.0fms",
                        fn.__name__, trigger, duration_ms,
                    )
                else:
                    logger.debug(
                        "Callback %s [trigger=%s] completed in %.1fms",
                        fn.__name__, trigger, duration_ms,
                    )
                return result
            except Exception as e:
                duration_ms = (time.monotonic() - start) * 1000
                logger.error(
                    "Callback %s [trigger=%s] failed after %.0fms: %s\n%s",
                    fn.__name__, trigger, duration_ms,
                    str(e), traceback.format_exc(),
                )
                raise
        return wrapper
    return decorator


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
            trigger = _get_trigger()
            start = time.monotonic()
            try:
                result = fn(*args, **kwargs)
                duration_ms = (time.monotonic() - start) * 1000
                if duration_ms > 50:
                    logger.info(
                        "Callback %s [trigger=%s] completed in %.0fms",
                        fn.__name__, trigger, duration_ms,
                    )
                else:
                    logger.debug(
                        "Callback %s [trigger=%s] completed in %.1fms",
                        fn.__name__, trigger, duration_ms,
                    )
                return result
            except Exception as e:
                duration_ms = (time.monotonic() - start) * 1000
                logger.error(
                    "Callback %s [trigger=%s] failed after %.0fms: %s\n%s",
                    fn.__name__, trigger, duration_ms,
                    str(e), traceback.format_exc(),
                )
                return _error_card(fallback_message, str(e))
        return wrapper
    return decorator


def _get_trigger():
    """Get the triggering input ID for the current callback, or 'unknown'."""
    try:
        triggered = ctx.triggered_id
        return str(triggered) if triggered else "initial"
    except Exception:
        return "unknown"


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
