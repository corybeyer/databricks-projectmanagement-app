"""Sprint Charts — velocity and burndown."""

import plotly.graph_objects as go
from charts.theme import COLORS, apply_theme


def velocity_chart(velocity_df):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=velocity_df["sprint_name"], y=velocity_df["committed_points"],
        name="Committed",
        marker=dict(color=COLORS["border"], line=dict(width=0)), opacity=0.5,
    ))
    fig.add_trace(go.Bar(
        x=velocity_df["sprint_name"], y=velocity_df["completed_points"],
        name="Completed",
        marker=dict(color=COLORS["green"], line=dict(width=0)),
    ))
    if len(velocity_df) >= 3:
        rolling_avg = velocity_df["completed_points"].rolling(3).mean()
        fig.add_trace(go.Scatter(
            x=velocity_df["sprint_name"], y=rolling_avg,
            name="3-Sprint Avg",
            line=dict(color=COLORS["accent"], width=2, dash="dot"), mode="lines",
        ))
    fig.update_layout(
        barmode="overlay",
        legend=dict(orientation="h", y=1.1, font=dict(size=11)),
        yaxis_title="Story Points",
    )
    return apply_theme(fig)


def burndown_chart(burndown_df, sprint_name="Sprint"):
    if burndown_df.empty:
        return go.Figure()
    total = burndown_df["total_points"].iloc[0]
    days = len(burndown_df)
    ideal_line = [total - (total / (days - 1)) * i for i in range(days)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=burndown_df["burn_date"], y=ideal_line,
        name="Ideal", line=dict(color=COLORS["text_dim"], width=1, dash="dash"), mode="lines",
    ))
    fig.add_trace(go.Scatter(
        x=burndown_df["burn_date"], y=burndown_df["remaining_points"],
        name="Actual", line=dict(color=COLORS["accent"], width=3),
        mode="lines+markers", marker=dict(size=6),
        fill="tozeroy", fillcolor="rgba(99, 102, 241, 0.08)",
    ))
    fig.update_layout(
        title=f"{sprint_name} Burndown", yaxis_title="Remaining Points",
        legend=dict(orientation="h", y=1.1),
    )
    return apply_theme(fig)
