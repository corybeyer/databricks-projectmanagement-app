"""
Visualization Components
========================
Reusable Plotly chart builders for the PM dashboard.
Each function returns a plotly.graph_objects.Figure.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta

# ─── Theme ──────────────────────────────────────────────────
COLORS = {
    "bg": "#0f1218",
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


# ─── Portfolio Health Donut ─────────────────────────────────
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


# ─── Gantt Timeline ────────────────────────────────────────
def gantt_chart(phases_df):
    """
    Build a Gantt chart from phases dataframe.
    Expects columns: name, start_date, end_date, status, delivery_method
    """
    color_map = {
        "waterfall": COLORS["purple"],
        "agile": COLORS["yellow"],
        "hybrid": COLORS["orange"],
    }

    fig = go.Figure()
    for i, row in phases_df.iterrows():
        color = color_map.get(row.get("delivery_method", "waterfall"), COLORS["blue"])
        opacity = 1.0 if row.get("status") != "not_started" else 0.4

        fig.add_trace(go.Bar(
            x=[pd.to_datetime(row["end_date"]) - pd.to_datetime(row["start_date"])],
            y=[row["name"]],
            base=[pd.to_datetime(row["start_date"])],
            orientation="h",
            marker=dict(color=color, opacity=opacity, line=dict(width=0)),
            hovertemplate=(
                f"<b>{row['name']}</b><br>"
                f"{row['start_date']} → {row['end_date']}<br>"
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


# ─── Velocity Chart ─────────────────────────────────────────
def velocity_chart(velocity_df):
    """
    Bar chart showing committed vs completed points per sprint.
    Expects columns: sprint_name, committed_points, completed_points
    """
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=velocity_df["sprint_name"],
        y=velocity_df["committed_points"],
        name="Committed",
        marker=dict(color=COLORS["border"], line=dict(width=0)),
        opacity=0.5,
    ))

    fig.add_trace(go.Bar(
        x=velocity_df["sprint_name"],
        y=velocity_df["completed_points"],
        name="Completed",
        marker=dict(color=COLORS["green"], line=dict(width=0)),
    ))

    # Rolling average line
    if len(velocity_df) >= 3:
        rolling_avg = velocity_df["completed_points"].rolling(3).mean()
        fig.add_trace(go.Scatter(
            x=velocity_df["sprint_name"],
            y=rolling_avg,
            name="3-Sprint Avg",
            line=dict(color=COLORS["accent"], width=2, dash="dot"),
            mode="lines",
        ))

    fig.update_layout(
        barmode="overlay",
        legend=dict(orientation="h", y=1.1, font=dict(size=11)),
        yaxis_title="Story Points",
    )
    return apply_theme(fig)


# ─── Burndown Chart ─────────────────────────────────────────
def burndown_chart(burndown_df, sprint_name="Sprint"):
    """
    Line chart showing remaining vs ideal burndown.
    Expects columns: burn_date, remaining_points, total_points
    """
    if burndown_df.empty:
        return go.Figure()

    total = burndown_df["total_points"].iloc[0]
    days = len(burndown_df)
    ideal_line = [total - (total / (days - 1)) * i for i in range(days)]

    fig = go.Figure()

    # Ideal burndown
    fig.add_trace(go.Scatter(
        x=burndown_df["burn_date"], y=ideal_line,
        name="Ideal", line=dict(color=COLORS["text_dim"], width=1, dash="dash"),
        mode="lines",
    ))

    # Actual burndown
    fig.add_trace(go.Scatter(
        x=burndown_df["burn_date"], y=burndown_df["remaining_points"],
        name="Actual", line=dict(color=COLORS["accent"], width=3),
        mode="lines+markers",
        marker=dict(size=6),
        fill="tozeroy",
        fillcolor="rgba(99, 102, 241, 0.08)",
    ))

    fig.update_layout(
        title=f"{sprint_name} Burndown",
        yaxis_title="Remaining Points",
        legend=dict(orientation="h", y=1.1),
    )
    return apply_theme(fig)


# ─── Budget Burn Chart ──────────────────────────────────────
def budget_burn_chart(projects_df):
    """
    Horizontal bar showing budget spent vs total per project.
    Expects columns: name, budget_spent, budget_total
    """
    fig = go.Figure()

    # Total budget bars (background)
    fig.add_trace(go.Bar(
        y=projects_df["name"],
        x=projects_df["budget_total"],
        orientation="h",
        name="Total Budget",
        marker=dict(color=COLORS["surface"], line=dict(color=COLORS["border"], width=1)),
    ))

    # Spent bars (overlay)
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
        y=projects_df["name"],
        x=projects_df["budget_spent"],
        orientation="h",
        name="Spent",
        marker=dict(color=colors, line=dict(width=0)),
    ))

    fig.update_layout(
        barmode="overlay",
        yaxis=dict(autorange="reversed"),
        xaxis=dict(tickprefix="$", tickformat=",.0f"),
        legend=dict(orientation="h", y=1.1),
        height=max(200, len(projects_df) * 45),
    )
    return apply_theme(fig)


# ─── Strategic Bubble Chart ─────────────────────────────────
def strategic_bubble_chart(projects_df):
    """
    Bubble chart: X=effort, Y=strategic value, Size=budget.
    Expects columns: name, strategic_value, effort_score, budget_total, health
    """
    color_map = {"green": COLORS["green"], "yellow": COLORS["yellow"], "red": COLORS["red"]}

    fig = go.Figure()
    for _, row in projects_df.iterrows():
        fig.add_trace(go.Scatter(
            x=[row.get("effort_score", 5)],
            y=[row.get("strategic_value", 5)],
            mode="markers+text",
            marker=dict(
                size=max(20, row.get("budget_total", 100000) / 8000),
                color=color_map.get(row.get("health", "green"), COLORS["blue"]),
                opacity=0.7,
                line=dict(color="white", width=1),
            ),
            text=row["name"][:12],
            textposition="middle center",
            textfont=dict(size=9, color="white"),
            hovertemplate=(
                f"<b>{row['name']}</b><br>"
                f"Value: {row.get('strategic_value', 'N/A')}<br>"
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


# ─── Risk Heatmap ───────────────────────────────────────────
def risk_heatmap(risks_df):
    """
    5x5 heatmap of probability vs impact.
    Expects columns: title, probability (1-5), impact (1-5)
    """
    # Build 5x5 matrix
    matrix = [[0] * 5 for _ in range(5)]
    annotations = [[[] for _ in range(5)] for _ in range(5)]

    for _, row in risks_df.iterrows():
        p = int(row["probability"]) - 1
        i = int(row["impact"]) - 1
        if 0 <= p < 5 and 0 <= i < 5:
            matrix[i][p] += 1
            annotations[i][p].append(row["title"][:15])

    # Custom colorscale: green → yellow → red
    colorscale = [
        [0.0, COLORS["surface"]],
        [0.25, "rgba(34,197,94,0.2)"],
        [0.5, "rgba(234,179,8,0.3)"],
        [0.75, "rgba(239,68,68,0.3)"],
        [1.0, "rgba(239,68,68,0.6)"],
    ]

    fig = go.Figure(go.Heatmap(
        z=matrix,
        x=["Very Low", "Low", "Medium", "High", "Critical"],
        y=["Very Low", "Low", "Medium", "High", "Critical"],
        colorscale=colorscale,
        showscale=False,
        hovertemplate="Probability: %{x}<br>Impact: %{y}<br>Count: %{z}<extra></extra>",
    ))

    # Add risk labels
    for i in range(5):
        for j in range(5):
            if annotations[i][j]:
                fig.add_annotation(
                    x=j, y=i,
                    text="<br>".join(annotations[i][j]),
                    showarrow=False,
                    font=dict(size=9, color=COLORS["text_muted"]),
                )

    fig.update_layout(
        xaxis=dict(title="Probability →", side="bottom"),
        yaxis=dict(title="Impact →"),
        height=350,
    )
    return apply_theme(fig)


# ─── Resource Utilization Bars ──────────────────────────────
def resource_utilization_chart(resource_df):
    """
    Stacked horizontal bars showing allocation per person across projects.
    Expects columns: display_name, project_name, allocation_pct
    """
    people = resource_df["display_name"].unique()
    projects = resource_df["project_name"].unique()

    project_colors = {}
    color_palette = [COLORS["purple"], COLORS["green"], COLORS["yellow"],
                     COLORS["cyan"], COLORS["blue"], COLORS["orange"]]
    for i, proj in enumerate(projects):
        project_colors[proj] = color_palette[i % len(color_palette)]

    fig = go.Figure()
    for proj in projects:
        proj_data = resource_df[resource_df["project_name"] == proj]
        fig.add_trace(go.Bar(
            y=proj_data["display_name"],
            x=proj_data["allocation_pct"],
            orientation="h",
            name=proj,
            marker=dict(color=project_colors[proj]),
            hovertemplate=f"<b>{proj}</b><br>%{{x}}% allocated<extra></extra>",
        ))

    fig.update_layout(
        barmode="stack",
        xaxis=dict(title="Allocation %", range=[0, 130],
                   dtick=25),
        legend=dict(orientation="h", y=-0.2, font=dict(size=10)),
        height=max(200, len(people) * 60),
    )

    # Add 100% reference line
    fig.add_vline(x=100, line=dict(color=COLORS["red"], width=1, dash="dash"),
                  annotation_text="100%", annotation_font=dict(size=10, color=COLORS["red"]))

    return apply_theme(fig)


# ─── Cycle Time Distribution ────────────────────────────────
def cycle_time_chart(transitions_df):
    """
    Box plot of time spent in each status.
    Expects columns: from_status, hours_in_status
    """
    status_order = ["todo", "in_progress", "review"]
    filtered = transitions_df[transitions_df["from_status"].isin(status_order)]

    fig = go.Figure()
    for status in status_order:
        data = filtered[filtered["from_status"] == status]["hours_in_status"]
        fig.add_trace(go.Box(
            y=data, name=status.replace("_", " ").title(),
            marker=dict(color=COLORS["accent"]),
            boxmean=True,
        ))

    fig.update_layout(
        yaxis_title="Hours",
        showlegend=False,
    )
    return apply_theme(fig)


# ─── Roadmap Multi-Project Timeline ─────────────────────────
def roadmap_chart(projects_df):
    """
    Multi-project Gantt for portfolio roadmap view.
    Expects columns: name, portfolio_name, start_date, target_date, health, delivery_method
    """
    color_map = {"green": COLORS["green"], "yellow": COLORS["yellow"], "red": COLORS["red"]}

    fig = go.Figure()
    for i, row in projects_df.iterrows():
        color = color_map.get(row.get("health", "green"), COLORS["blue"])
        fig.add_trace(go.Bar(
            x=[pd.to_datetime(row["target_date"]) - pd.to_datetime(row["start_date"])],
            y=[f"{row['name']}<br><sub>{row.get('portfolio_name', '')}</sub>"],
            base=[pd.to_datetime(row["start_date"])],
            orientation="h",
            marker=dict(color=color, opacity=0.8, line=dict(width=0)),
            hovertemplate=(
                f"<b>{row['name']}</b><br>"
                f"Portfolio: {row.get('portfolio_name', 'N/A')}<br>"
                f"{row['start_date']} → {row['target_date']}<br>"
                f"Method: {row.get('delivery_method', 'N/A')}<extra></extra>"
            ),
            showlegend=False,
        ))

    # Today marker
    fig.add_vline(x=datetime.now(), line=dict(color=COLORS["accent"], width=2, dash="dot"),
                  annotation_text="Today", annotation_font=dict(size=10, color=COLORS["accent"]))

    fig.update_layout(
        barmode="overlay",
        yaxis=dict(autorange="reversed"),
        xaxis=dict(type="date"),
        height=max(300, len(projects_df) * 55),
    )
    return apply_theme(fig)
