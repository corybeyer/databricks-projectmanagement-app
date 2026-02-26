"""Analytics Charts — risk heatmap, cycle time, resource utilization."""

import plotly.graph_objects as go
from charts.theme import COLORS, apply_theme


def risk_heatmap(risks_df):
    matrix = [[0] * 5 for _ in range(5)]
    annotations = [[[] for _ in range(5)] for _ in range(5)]
    for _, row in risks_df.iterrows():
        p = int(row["probability"]) - 1
        i = int(row["impact"]) - 1
        if 0 <= p < 5 and 0 <= i < 5:
            matrix[i][p] += 1
            annotations[i][p].append(row["title"][:15])
    colorscale = [
        [0.0, COLORS["surface"]], [0.25, "rgba(34,197,94,0.2)"],
        [0.5, "rgba(234,179,8,0.3)"], [0.75, "rgba(239,68,68,0.3)"],
        [1.0, "rgba(239,68,68,0.6)"],
    ]
    fig = go.Figure(go.Heatmap(
        z=matrix,
        x=["Very Low", "Low", "Medium", "High", "Critical"],
        y=["Very Low", "Low", "Medium", "High", "Critical"],
        colorscale=colorscale, showscale=False,
        hovertemplate="Probability: %{x}<br>Impact: %{y}<br>Count: %{z}<extra></extra>",
    ))
    for i in range(5):
        for j in range(5):
            if annotations[i][j]:
                fig.add_annotation(
                    x=j, y=i, text="<br>".join(annotations[i][j]),
                    showarrow=False, font=dict(size=9, color=COLORS["text_muted"]),
                )
    fig.update_layout(
        xaxis=dict(title="Probability →", side="bottom"),
        yaxis=dict(title="Impact →"), height=350,
    )
    return apply_theme(fig)


def risk_heatmap_residual(risks_df):
    """Same as risk_heatmap but uses residual_probability and residual_impact columns."""
    # Filter to rows that have residual values
    filtered = risks_df.dropna(subset=["residual_probability", "residual_impact"])
    matrix = [[0] * 5 for _ in range(5)]
    annotations = [[[] for _ in range(5)] for _ in range(5)]
    for _, row in filtered.iterrows():
        p = int(row["residual_probability"]) - 1
        i = int(row["residual_impact"]) - 1
        if 0 <= p < 5 and 0 <= i < 5:
            matrix[i][p] += 1
            annotations[i][p].append(row["title"][:15])
    colorscale = [
        [0.0, COLORS["surface"]], [0.25, "rgba(34,197,94,0.2)"],
        [0.5, "rgba(234,179,8,0.3)"], [0.75, "rgba(239,68,68,0.3)"],
        [1.0, "rgba(239,68,68,0.6)"],
    ]
    fig = go.Figure(go.Heatmap(
        z=matrix,
        x=["Very Low", "Low", "Medium", "High", "Critical"],
        y=["Very Low", "Low", "Medium", "High", "Critical"],
        colorscale=colorscale, showscale=False,
        hovertemplate="Probability: %{x}<br>Impact: %{y}<br>Count: %{z}<extra></extra>",
    ))
    for i in range(5):
        for j in range(5):
            if annotations[i][j]:
                fig.add_annotation(
                    x=j, y=i, text="<br>".join(annotations[i][j]),
                    showarrow=False, font=dict(size=9, color=COLORS["text_muted"]),
                )
    fig.update_layout(
        xaxis=dict(title="Residual Probability →", side="bottom"),
        yaxis=dict(title="Residual Impact →"), height=350,
    )
    return apply_theme(fig)


def cycle_time_chart(transitions_df):
    status_order = ["todo", "in_progress", "review"]
    filtered = transitions_df[transitions_df["from_status"].isin(status_order)]
    fig = go.Figure()
    for status in status_order:
        data = filtered[filtered["from_status"] == status]["hours_in_status"]
        fig.add_trace(go.Box(
            y=data, name=status.replace("_", " ").title(),
            marker=dict(color=COLORS["accent"]), boxmean=True,
        ))
    fig.update_layout(yaxis_title="Hours", showlegend=False)
    return apply_theme(fig)


def resource_utilization_chart(resource_df):
    people = resource_df["display_name"].unique()
    projects = resource_df["project_name"].unique()
    color_palette = [COLORS["purple"], COLORS["green"], COLORS["yellow"],
                     COLORS["cyan"], COLORS["blue"], COLORS["orange"]]
    project_colors = {proj: color_palette[i % len(color_palette)] for i, proj in enumerate(projects)}
    fig = go.Figure()
    for proj in projects:
        proj_data = resource_df[resource_df["project_name"] == proj]
        fig.add_trace(go.Bar(
            y=proj_data["display_name"], x=proj_data["allocation_pct"],
            orientation="h", name=proj,
            marker=dict(color=project_colors[proj]),
            hovertemplate=f"<b>{proj}</b><br>%{{x}}% allocated<extra></extra>",
        ))
    fig.update_layout(
        barmode="stack", xaxis=dict(title="Allocation %", range=[0, 130], dtick=25),
        legend=dict(orientation="h", y=-0.2, font=dict(size=10)),
        height=max(200, len(people) * 60),
    )
    fig.add_vline(x=100, line=dict(color=COLORS["red"], width=1, dash="dash"),
                  annotation_text="100%", annotation_font=dict(size=10, color=COLORS["red"]))
    return apply_theme(fig)
