"""Export Service — data export to Excel."""

import io
import pandas as pd


def to_excel(df: pd.DataFrame, filename: str = "export") -> bytes:
    """Export DataFrame to Excel bytes with formatting.

    Args:
        df: Data to export
        filename: Base filename (without extension, used for sheet name)
    Returns:
        Excel file as bytes (suitable for dcc.Download)
    """
    from openpyxl.utils import get_column_letter

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        display_df = df.copy()
        display_df.columns = [
            col.replace("_", " ").title() for col in display_df.columns
        ]
        sheet_name = filename[:31]  # Excel sheet name max 31 chars
        display_df.to_excel(writer, sheet_name=sheet_name, index=False)

        # Auto-fit column widths
        worksheet = writer.sheets[sheet_name]
        for idx, col in enumerate(display_df.columns):
            max_len = max(
                display_df[col].astype(str).map(len).max() if not display_df.empty else 0,
                len(col)
            ) + 2
            worksheet.column_dimensions[get_column_letter(idx + 1)].width = min(max_len, 50)

    return output.getvalue()


def to_pdf(content: str) -> bytes:
    """Export content to PDF bytes. Placeholder."""
    raise NotImplementedError("PDF export not yet implemented.")
