"""Portfolio Charts — health donut, budget burn, strategic bubble, roadmap."""

import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from charts.theme import COLORS, LAYOUT_DEFAULTS, apply_theme


def portfolio_health_donut(green_count, yellow_count, red_count, planning_count=0):
    labels = ["On Track", "At Risk", "Off Track", "Planning"]
    values = [green_count, yellow_count, red_count, planning_count]
    colors = [COLORS["green"], COLORS["yellow"], COLORS["red"], COLORS["blue"]]

    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.65,
        marker=dict(colors=colors, line=dict(color=COLORS["bg"], width=2)),
        textinfo="value",
        textfont=dict(size=14, color="white"),
        hovertemplate="<b>%{label}</b><br>%{value} projects<extra></extra>",
    ))
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", y=-0.1, font=dict(size=11, color=COLORS["text_muted"])),
        **{k: v for k, v in LAYOUT_DEFAULTS.items() if k not in ["xaxis", "yaxis"]},
    )
    fig.add_annotation(
        text=f"<b>{sum(values)}</b><br><span style='font-size:11px;color:{COLORS['text_dim']}'>projects</span>",
        showarrow=False, font=dict(size=22, color=COLORS["text"]),
    )
    return fig


def budget_burn_chart(projects_df):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=projects_df["name"], x=projects_df["budget_total"],
        orientation="h", name="Total Budget",
        marker=dict(color=COLORS["surface"], line=dict(color=COLORS["border"], width=1)),
    ))

    colors = []
    for _, row in projects_df.iterrows():
        pct = row["budget_spent"] / row["budget_total"] if row["budget_total"] > 0 else 0
        if pct > 0.9:
            colors.append(COLORS["red"])
        elif pct > 0.75:
            colors.append(COLORS["yellow"])
        else:
            colors.append(COLORS["green"])

    fig.add_trace(go.Bar(
        y=projects_df["name"], x=projects_df["budget_spent"],
        orientation="h", name="Spent",
        marker=dict(color=colors, line=dict(width=0)),
    ))
    fig.update_layout(
        barmode="overlay", yaxis=dict(autorange="reversed"),
        xaxis=dict(tickprefix="$", tickformat=",.0f"),
        legend=dict(orientation="h", y=1.1),
        height=max(200, len(projects_df) * 45),
    )
    return apply_theme(fig)


def strategic_bubble_chart(projects_df):
    color_map = {"green": COLORS["green"], "yellow": COLORS["yellow"], "red": COLORS["red"]}
    fig = go.Figure()
    for _, row in projects_df.iterrows():
        fig.add_trace(go.Scatter(
            x=[row.get("effort_score", 5)], y=[row.get("strategic_value", 5)],
            mode="markers+text",
            marker=dict(
                size=max(20, row.get("budget_total", 100000) / 8000),
                color=color_map.get(row.get("health", "green"), COLORS["blue"]),
                opacity=0.7, line=dict(color="white", width=1),
            ),
            text=row["name"][:12], textposition="middle center",
            textfont=dict(size=9, color="white"),
            hovertemplate=(
                f"<b>{row['name']}</b><br>Value: {row.get('strategic_value', 'N/A')}<br>"
                f"Effort: {row.get('effort_score', 'N/A')}<br>"
                f"Budget: ${row.get('budget_total', 0):,.0f}<extra></extra>"
            ),
            showlegend=False,
        ))
    fig.update_layout(
        xaxis=dict(title="Effort →", range=[0, 10]),
        yaxis=dict(title="Strategic Value →", range=[0, 10]),
    )
    return apply_theme(fig)


def roadmap_chart(projects_df):
    color_map = {"green": COLORS["green"], "yellow": COLORS["yellow"], "red": COLORS["red"]}
    fig = go.Figure()
    for _, row in projects_df.iterrows():
        color = color_map.get(row.get("health", "green"), COLORS["blue"])
        fig.add_trace(go.Bar(
            x=[pd.to_datetime(row["target_date"]) - pd.to_datetime(row["start_date"])],
            y=[f"{row['name']}<br><sub>{row.get('portfolio_name', '')}</sub>"],
            base=[pd.to_datetime(row["start_date"])],
            orientation="h",
            marker=dict(color=color, opacity=0.8, line=dict(width=0)),
            hovertemplate=(
                f"<b>{row['name']}</b><br>Portfolio: {row.get('portfolio_name', 'N/A')}<br>"
                f"{row['start_date']} → {row['target_date']}<extra></extra>"
            ),
            showlegend=False,
        ))
    fig.add_vline(x=datetime.now(), line=dict(color=COLORS["accent"], width=2, dash="dot"),
                  annotation_text="Today", annotation_font=dict(size=10, color=COLORS["accent"]))
    fig.update_layout(
        barmode="overlay", yaxis=dict(autorange="reversed"),
        xaxis=dict(type="date"), height=max(300, len(projects_df) * 55),
    )
    return apply_theme(fig)
