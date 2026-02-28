"""Timesheet Charts — time tracking visualizations."""

import plotly.graph_objects as go
from charts.theme import COLORS, apply_theme


def hours_by_task_chart(entries_df):
    """Build a horizontal bar chart of hours per task.

    Args:
        entries_df: DataFrame with 'task_title' and 'hours' columns.

    Returns:
        go.Figure
    """
    if entries_df.empty or "task_title" not in entries_df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No time data available", showarrow=False,
                           font=dict(color=COLORS["text_muted"], size=14))
        return apply_theme(fig)

    summary = entries_df.groupby("task_title", as_index=False)["hours"].sum()
    summary = summary.sort_values("hours", ascending=True)

    fig = go.Figure(go.Bar(
        x=summary["hours"],
        y=summary["task_title"],
        orientation="h",
        marker_color=COLORS["accent"],
        hovertemplate="%{y}<br>%{x:.1f} hours<extra></extra>",
    ))
    fig.update_layout(
        xaxis=dict(title="Hours Logged"),
        yaxis=dict(title=""),
        height=max(250, len(summary) * 35 + 80),
    )
    return apply_theme(fig)
