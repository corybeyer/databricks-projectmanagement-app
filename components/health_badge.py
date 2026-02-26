"""Health Badge — status indicator component."""

from dash import html
from charts.theme import COLORS


def health_badge(status):
    colors = {"green": COLORS["green"], "yellow": COLORS["yellow"], "red": COLORS["red"]}
    labels = {"green": "ON TRACK", "yellow": "AT RISK", "red": "OFF TRACK"}
    color = colors.get(status, COLORS["text_muted"])
    label = labels.get(status, status.upper())
    return html.Span([
        html.Span("● ", style={"color": color}),
        html.Span(label, style={"color": color}),
    ], className="health-badge")
