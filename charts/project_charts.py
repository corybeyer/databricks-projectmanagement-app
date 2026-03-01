"""Project Charts — Gantt timeline."""

import plotly.graph_objects as go
import pandas as pd
from charts.theme import COLORS, apply_theme


def gantt_chart(phases_df):
    color_map = {
        "waterfall": COLORS["purple"],
        "agile": COLORS["yellow"],
        "hybrid": COLORS["orange"],
    }
    fig = go.Figure()
    for _, row in phases_df.iterrows():
        color = color_map.get(row.get("delivery_method", "waterfall"), COLORS["blue"])
        opacity = 1.0 if row.get("status") != "not_started" else 0.4
        fig.add_trace(go.Bar(
            x=[(pd.to_datetime(row["end_date"]) - pd.to_datetime(row["start_date"])).total_seconds() * 1000],
            y=[row["name"]], base=[pd.to_datetime(row["start_date"])],
            orientation="h",
            marker=dict(color=color, opacity=opacity, line=dict(width=0)),
            hovertemplate=(
                f"<b>{row['name']}</b><br>{row['start_date']} → {row['end_date']}<br>"
                f"Method: {row.get('delivery_method', 'N/A')}<br>"
                f"Status: {row.get('status', 'N/A')}<extra></extra>"
            ),
            showlegend=False,
        ))
    fig.update_layout(
        barmode="overlay",
        yaxis=dict(autorange="reversed", categoryorder="array",
                   categoryarray=phases_df["name"].tolist()),
        xaxis=dict(type="date"),
        height=max(250, len(phases_df) * 50),
    )
    return apply_theme(fig)
