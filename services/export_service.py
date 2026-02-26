"""Export Service — data export (placeholder)."""

import pandas as pd


def to_excel(df: pd.DataFrame, filename: str) -> bytes:
    """Export DataFrame to Excel bytes. Placeholder."""
    raise NotImplementedError("Excel export not yet implemented.")


def to_pdf(content: str) -> bytes:
    """Export content to PDF bytes. Placeholder."""
    raise NotImplementedError("PDF export not yet implemented.")
