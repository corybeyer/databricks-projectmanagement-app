"""
Chart Theme — Colors and Layout Defaults
==========================================
Single source of truth for all color values and chart styling.
"""

COLORS = {
    "bg": "#0a0d12",
    "surface": "#161b24",
    "border": "#1e293b",
    "text": "#e2e8f0",
    "text_muted": "#94a3b8",
    "text_dim": "#64748b",
    "accent": "#6366f1",
    "green": "#22c55e",
    "yellow": "#eab308",
    "red": "#ef4444",
    "blue": "#3b82f6",
    "purple": "#a855f7",
    "cyan": "#06b6d4",
    "orange": "#f97316",
}

ICON_COLORS = {
    "blue": "icon-blue",
    "green": "icon-green",
    "red": "icon-red",
    "yellow": "icon-yellow",
    "purple": "icon-purple",
    "cyan": "icon-cyan",
    "orange": "icon-orange",
}

LAYOUT_DEFAULTS = dict(
    paper_bgcolor=COLORS["bg"],
    plot_bgcolor=COLORS["surface"],
    font=dict(family="DM Sans, sans-serif", color=COLORS["text"], size=12),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
    yaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
)


def apply_theme(fig):
    """Apply consistent dark theme to any figure."""
    fig.update_layout(**LAYOUT_DEFAULTS)
    return fig
