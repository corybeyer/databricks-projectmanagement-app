"""Test fixtures for PM Hub."""

import pytest
import pandas as pd


@pytest.fixture
def sample_portfolios():
    return pd.DataFrame([
        {"portfolio_id": "pf-001", "name": "Test Portfolio", "owner": "Test",
         "status": "active", "health": "green", "project_count": 3,
         "avg_completion": 50, "total_spent": 100000, "total_budget": 200000},
    ])


@pytest.fixture
def sample_tasks():
    return pd.DataFrame([
        {"task_id": "t-001", "title": "Test task", "task_type": "story",
         "status": "todo", "story_points": 5, "priority": "medium"},
    ])
