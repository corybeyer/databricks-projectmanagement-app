"""Resource Charts — capacity planning and allocation visualizations."""

import plotly.graph_objects as go
from charts.theme import COLORS, apply_theme


def _allocation_bar_color(pct):
    """Return bar color based on allocation percentage."""
    if pct > 100:
        return COLORS["red"]
    elif pct >= 80:
        return COLORS["yellow"]
    return COLORS["green"]


def capacity_chart(capacity_df):
    """Build a horizontal bar chart showing total allocation per member.

    Args:
        capacity_df: DataFrame with 'display_name' and 'total_allocation' columns.

    Returns:
        go.Figure or None if data is insufficient.
    """
    if capacity_df.empty or "total_allocation" not in capacity_df.columns:
        return None

    names = capacity_df["display_name"].tolist()
    allocations = capacity_df["total_allocation"].tolist()
    colors = [_allocation_bar_color(a) for a in allocations]

    fig = go.Figure(go.Bar(
        y=names,
        x=allocations,
        orientation="h",
        marker=dict(color=colors),
        hovertemplate="<b>%{y}</b><br>%{x}% allocated<extra></extra>",
    ))
    fig.update_layout(
        xaxis=dict(title="Total Allocation %", range=[0, max(max(allocations, default=0) + 20, 130)], dtick=25),
        height=max(200, len(names) * 50),
    )
    fig.add_vline(
        x=100, line=dict(color=COLORS["red"], width=1, dash="dash"),
        annotation_text="100%", annotation_font=dict(size=10, color=COLORS["red"]),
    )
    return apply_theme(fig)
