"""
Logging Configuration
=====================
Structured logging to stdout/stderr (Databricks Apps requirement).
"""

import logging
import sys


def setup_logging(level: str = "INFO"):
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        root.addHandler(handler)
