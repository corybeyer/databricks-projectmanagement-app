---
name: dash-patterns
description: Dash (Plotly) development patterns for PM Hub. Auto-loads when Claude detects work on Dash pages, callbacks, layouts, or Plotly charts. Contains the canonical patterns, component conventions, and anti-patterns.
triggers:
  - dash
  - plotly
  - callback
  - layout
  - dbc
  - chart
  - figure
  - page
---

# PM Hub Dash Patterns

## Page Structure — The Canonical Pattern

Every page in PM Hub follows this exact structure:

```python
"""
{Page Title} Page
==================
Brief description.
"""

import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from utils.data_access import get_relevant_data
from utils.charts import relevant_chart_builder, COLORS

dash.register_page(__name__, path="/route", name="Page Title")


# ─── Components (private to this page) ─────────────────────
def _kpi_card(label, value, sub_text, color=None):
    """Small reusable component. Prefix with underscore."""
    return dbc.Card(
        dbc.CardBody([
            html.Div(label, className="kpi-label"),
            html.Div(str(value), className="kpi-value",
                     style={"color": color} if color else {}),
            html.Div(sub_text, className="kpi-sub"),
        ]),
        className="kpi-card",
    )


# ─── Layout (MUST be a function, not a variable) ───────────
def layout():
    data = get_relevant_data()

    return html.Div([
        # Page title
        html.H4("Page Title", className="page-title mb-3"),

        # KPI strip
        dbc.Row([
            dbc.Col(_kpi_card("Label", "Value", "subtext"), width=3),
        ], className="kpi-strip mb-4"),

        # Main content
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Section Title"),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=relevant_chart_builder(data),
                            config={"displayModeBar": False},
                        ),
                    ]),
                ]),
            ], width=8),
            dbc.Col([
                # Sidebar content
            ], width=4),
        ]),
    ])


# ─── Callbacks (below layout) ──────────────────────────────
@callback(
    Output("output-id", "children"),
    Input("input-id", "value"),
)
def update_something(value):
    # Callback logic
    return result
```

## Critical Rules

### DO
- `layout()` is always a **function** — it runs on each page load, fetching fresh data
- Import data functions from `utils/data_access.py`
- Import chart builders from `utils/charts.py`
- Use `dbc.Row` / `dbc.Col` / `dbc.Card` for all layout structure
- Use `dcc.Graph` with `config={"displayModeBar": False}` for clean charts
- Use `className` for styling — reference classes defined in `assets/custom.css`
- Prefix page-private components with underscore: `_kpi_card()`, `_task_row()`

### DON'T
- Never define `layout = html.Div(...)` as a variable (stale data)
- Never write SQL in page files
- Never build Plotly figures in page files
- Never hardcode colors — use `COLORS` dict from charts.py
- Never use `style={}` for static styling — use CSS classes
- Never use Streamlit patterns (st.write, st.columns, st.metric)

## Chart Builder Pattern

```python
# In utils/charts.py

def my_chart(df: pd.DataFrame) -> go.Figure:
    """
    Always: take DataFrame, return Figure.
    Always: call apply_theme() before returning.
    """
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["category"],
        y=df["value"],
        marker=dict(color=COLORS["accent"]),
    ))

    fig.update_layout(
        yaxis_title="Value",
    )

    return apply_theme(fig)
```

## Data Access Pattern

```python
# In utils/data_access.py

def get_things(filter_id: str = None) -> pd.DataFrame:
    """
    Always: return pd.DataFrame.
    Always: have a sample data fallback.
    """
    where = f"WHERE thing_id = '{filter_id}'" if filter_id else ""
    return query(f"""
        SELECT t.*, r.related_name
        FROM things t
        LEFT JOIN related r ON t.related_id = r.related_id
        {where}
        ORDER BY t.created_at DESC
    """)
```

## Callback Patterns

### Simple update
```python
@callback(
    Output("chart-container", "children"),
    Input("dropdown", "value"),
)
def update_chart(selected_value):
    data = get_filtered_data(selected_value)
    return dcc.Graph(figure=my_chart(data), config={"displayModeBar": False})
```

### Multiple outputs
```python
@callback(
    Output("kpi-1", "children"),
    Output("kpi-2", "children"),
    Output("chart", "children"),
    Input("project-selector", "value"),
)
def update_dashboard(project_id):
    data = get_project_detail(project_id)
    return (
        f"{data['completion']}%",
        f"${data['budget']:,.0f}",
        dcc.Graph(figure=project_chart(data)),
    )
```

## Component Hierarchy

```
dbc.Row                    ← Full-width row
└── dbc.Col(width=N)       ← Column (N out of 12)
    └── dbc.Card            ← Bordered container
        ├── dbc.CardHeader  ← Title bar
        └── dbc.CardBody    ← Content area
            ├── dcc.Graph   ← Plotly chart
            ├── html.Div    ← Custom HTML
            └── dbc.Table   ← Data table
```
