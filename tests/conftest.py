"""Test fixtures for PM Hub."""

import os
import pytest
import pandas as pd

# Force sample data mode for all tests
os.environ["USE_SAMPLE_DATA"] = "true"


@pytest.fixture(autouse=True)
def reset_sample_data():
    """Reset in-memory store before each test."""
    from models.sample_data import reset_store
    reset_store()
    yield
    reset_store()


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


@pytest.fixture
def user_email():
    return "test@pm-hub.local"
