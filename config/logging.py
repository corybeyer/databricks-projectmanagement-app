"""
Logging Configuration
=====================
Source-traceable logging with correlation IDs for request tracing.
Each Flask request gets an 8-char trace ID so you can grep a single
ID to see the full call chain (callback → service → repo → DB).

Format:
    2026-03-01 14:23:05 [ERROR] db.unity_catalog:execute_query:91 [t:a1b2c3d4] SQL error...
"""

import logging
import sys
import threading
import uuid

# Thread-local storage for trace IDs
_trace_local = threading.local()


def get_trace_id() -> str:
    """Return the current request's trace ID, or empty string if none."""
    return getattr(_trace_local, "trace_id", "")


def set_trace_id(trace_id: str = None) -> str:
    """Set a trace ID for the current thread. Generates one if not provided."""
    if trace_id is None:
        trace_id = uuid.uuid4().hex[:8]
    _trace_local.trace_id = trace_id
    return trace_id


def clear_trace_id():
    """Clear the trace ID for the current thread."""
    _trace_local.trace_id = ""


class TraceIdFilter(logging.Filter):
    """Inject trace_id into every log record."""

    def filter(self, record):
        tid = get_trace_id()
        record.trace_id = f" [t:{tid}]" if tid else ""
        return True


def setup_logging(level: str = "INFO"):
    """Configure root logger with source-traceable format and trace ID support."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates on reload
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)-5s] %(name)s:%(funcName)s:%(lineno)d"
        "%(trace_id)s %(message)s"
    ))
    handler.addFilter(TraceIdFilter())
    root.addHandler(handler)

    # Suppress noisy third-party loggers
    for noisy in ("werkzeug", "urllib3", "urllib3.connectionpool",
                  "httpcore", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
