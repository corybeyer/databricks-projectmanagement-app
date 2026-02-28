"""Export Button — download trigger component."""

from dash import html, dcc
import dash_bootstrap_components as dbc


def export_button(button_id, label="Export", download_id=None):
    dl_id = download_id or f"{button_id}-download"
    return html.Div([
        dbc.Button(
            [html.I(className="bi bi-download me-1"), label],
            id=button_id, size="sm", outline=True, color="secondary",
        ),
        dcc.Download(id=dl_id),
    ])
