"""App State — client-side dcc.Store components for cross-page state."""

from dash import dcc


def app_stores():
    """Return all application-level dcc.Store components.

    These maintain client-side state across page navigations.
    Pages read from these stores to filter data contextually.
    """
    return [
        # Active department context (for multi-department filtering)
        dcc.Store(id="active-department-store", storage_type="session", data=None),
        # Active portfolio context (set when user drills into a portfolio)
        dcc.Store(id="active-portfolio-store", storage_type="session", data=None),
        # Active project context (set when user selects/drills into a project)
        dcc.Store(id="active-project-store", storage_type="session", data=None),
        # Active sprint context (set when user selects a sprint)
        dcc.Store(id="active-sprint-store", storage_type="session", data=None),
        # Current user context (email, role, permissions — set on app load)
        dcc.Store(id="user-context-store", storage_type="session", data=None),
        # Toast notification store (for toast system — Phase 1.1 will use this)
        dcc.Store(id="toast-store", storage_type="memory", data=None),
    ]
