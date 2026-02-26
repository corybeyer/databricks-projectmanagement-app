"""Chart builder tests — verify functions return go.Figure."""

import plotly.graph_objects as go
import pandas as pd
from charts.portfolio_charts import portfolio_health_donut, budget_burn_chart
from charts.sprint_charts import velocity_chart, burndown_chart


def test_portfolio_health_donut():
    fig = portfolio_health_donut(3, 1, 1)
    assert isinstance(fig, go.Figure)


def test_budget_burn_chart():
    df = pd.DataFrame([
        {"name": "Project A", "budget_spent": 50000, "budget_total": 100000},
        {"name": "Project B", "budget_spent": 80000, "budget_total": 100000},
    ])
    fig = budget_burn_chart(df)
    assert isinstance(fig, go.Figure)


def test_velocity_chart():
    df = pd.DataFrame([
        {"sprint_name": "Sprint 1", "committed_points": 20, "completed_points": 18},
        {"sprint_name": "Sprint 2", "committed_points": 22, "completed_points": 22},
    ])
    fig = velocity_chart(df)
    assert isinstance(fig, go.Figure)


def test_burndown_chart_empty():
    fig = burndown_chart(pd.DataFrame())
    assert isinstance(fig, go.Figure)
