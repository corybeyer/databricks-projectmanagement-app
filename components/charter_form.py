"""Charter Form — creation form for new project charters."""

from dash import html
import dash_bootstrap_components as dbc


def charter_form():
    return dbc.Card([
        dbc.CardHeader([html.H4("Create New Charter", className="mb-0")]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Project Name"),
                    dbc.Input(id="charter-project-name", type="text",
                              placeholder="e.g., Unity Catalog Migration"),
                ], width=6),
                dbc.Col([
                    dbc.Label("Delivery Method"),
                    dbc.Select(id="charter-method", options=[
                        {"label": "Waterfall — Sequential phases with gate approvals", "value": "waterfall"},
                        {"label": "Agile — Sprint-based iterative delivery", "value": "agile"},
                        {"label": "Hybrid — Waterfall governance + Agile execution", "value": "hybrid"},
                    ], value="hybrid"),
                ], width=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Business Case"),
                    dbc.Textarea(id="charter-business-case", rows=3,
                                 placeholder="Why does this project exist? What problem does it solve?"),
                ], width=12),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Objectives (one per line)"),
                    dbc.Textarea(id="charter-objectives", rows=4,
                                 placeholder="1. Migrate 100% of tables by Q2\n2. Implement row-level security"),
                ], width=6),
                dbc.Col([
                    dbc.Label("Success Criteria"),
                    dbc.Textarea(id="charter-success", rows=4,
                                 placeholder="How do we know this project succeeded?"),
                ], width=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("In Scope"),
                    dbc.Textarea(id="charter-scope-in", rows=3, placeholder="What IS included"),
                ], width=6),
                dbc.Col([
                    dbc.Label("Out of Scope"),
                    dbc.Textarea(id="charter-scope-out", rows=3, placeholder="What is explicitly NOT included"),
                ], width=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Key Stakeholders"),
                    dbc.Textarea(id="charter-stakeholders", rows=2,
                                 placeholder="CIO (Sponsor), VP Data (Owner)"),
                ], width=6),
                dbc.Col([
                    dbc.Label("Known Risks"),
                    dbc.Textarea(id="charter-risks", rows=2,
                                 placeholder="Resource contention, scope changes"),
                ], width=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([dbc.Label("Budget"), dbc.Input(id="charter-budget", type="text", placeholder="$420,000")], width=3),
                dbc.Col([dbc.Label("Timeline"), dbc.Input(id="charter-timeline", type="text", placeholder="Jan 2026 — Aug 2026")], width=3),
                dbc.Col([dbc.Label("Sponsor / Approver"), dbc.Input(id="charter-approver", type="text", placeholder="VP Data & Analytics")], width=3),
                dbc.Col([html.Br(), dbc.Button("Create Charter", id="charter-submit", color="primary", className="w-100 mt-1")], width=3),
            ]),
        ]),
    ], className="charter-form-card mb-4")
