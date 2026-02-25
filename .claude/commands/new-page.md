---
name: new-page
description: Scaffold a new Dash page following PM Hub architecture patterns. Creates the page file, adds stub query functions to data_access.py, and adds the nav link to app.py.
arguments:
  - name: name
    description: "Page name in kebab-case (e.g., risk-register, sprint-board)"
    required: true
  - name: route
    description: "URL route (e.g., /risks, /sprint)"
    required: true
  - name: title
    description: "Display title for the page (e.g., Risk Register)"
    required: true
---

Scaffold a new Dash page with all standard PM Hub patterns.

## Steps

1. Convert the kebab-case name to a Python filename: `pages/{name_with_underscores}.py`

2. Create the page file with the standard template:
   - `dash.register_page()` with the route and title
   - Import from `utils/data_access` and `utils/charts`
   - Import `dash_bootstrap_components as dbc`
   - A `layout()` function (NOT a variable)
   - Placeholder KPI strip
   - Placeholder main content area
   - Standard card layout using dbc.Row/dbc.Col/dbc.Card

3. Add stub query function(s) to `utils/data_access.py`:
   - Function named `get_{plural_name}()` that returns a DataFrame
   - Include a sample data fallback in `_sample_data_fallback()`

4. Add a nav link in `app.py` in the appropriate sidebar section:
   - Determine which section (PORTFOLIO, PROJECTS, EXECUTION, ANALYTICS)
   - Add `make_nav_link("{title}", "{route}", "icon-name")`

5. Report what was created and suggest next steps.

## Page Template

```python
"""
{Title} Page
{'=' * (len(title) + 5)}
Brief description of what this page shows.
"""

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
from utils.data_access import get_{name}
from utils.charts import COLORS

dash.register_page(__name__, path="{route}", name="{title}")

def layout():
    data = get_{name}()
    
    return html.Div([
        html.H4("{title}", className="page-title mb-3"),
        
        # KPI Strip
        dbc.Row([
            # Add KPI cards here
        ], className="kpi-strip mb-4"),
        
        # Main Content
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("{title}"),
                    dbc.CardBody([
                        html.Div("Content goes here", className="text-muted"),
                    ]),
                ]),
            ], width=12),
        ]),
    ])
```

## Example

```
/new-page risk-register /risks "Risk Register"
```

Creates:
- `pages/risk_register.py` with standard layout
- `get_risk_register()` stub in `utils/data_access.py`
- Nav link in app.py under ANALYTICS section
