"""
Project Charters Page
======================
View and create formal project charter documents.
Supports waterfall, agile, and hybrid delivery methods.
"""

import dash
from dash import html, dcc, callback, Input, Output, State, ALL
import dash_bootstrap_components as dbc
from utils.data_access import get_project_charter, get_portfolio_projects, get_portfolios
from utils.charts import COLORS

dash.register_page(__name__, path="/charters", name="Project Charters")


# ─── Charter Display Card ──────────────────────────────────
def charter_section(title, content, icon=""):
    return html.Div([
        html.Div([
            html.Span(icon + " " if icon else ""),
            html.Span(title, className="charter-section-title"),
        ], className="charter-section-header"),
        html.Div(content, className="charter-section-body"),
    ], className="charter-section")


def charter_display(charter):
    """Render a full project charter document."""
    if charter is None or charter.empty:
        return html.Div("No charter found.", className="text-muted p-4")

    c = charter.iloc[0]

    method_colors = {
        "waterfall": COLORS["purple"],
        "agile": COLORS["yellow"],
        "hybrid": COLORS["accent"],
    }
    method = c.get("delivery_method", "hybrid").lower()
    method_color = method_colors.get(method.split(" ")[0], COLORS["accent"])

    return dbc.Card([
        # Charter Header
        dbc.CardHeader([
            html.Div([
                html.H3(c.get("project_name", "Project Charter"), className="charter-title"),
                html.Div([
                    html.Span(
                        c.get("delivery_method", "Hybrid"),
                        className="method-badge",
                        style={"backgroundColor": f"{method_color}20", "color": method_color},
                    ),
                    html.Span(
                        f"v{c.get('version', 1)}",
                        className="version-badge",
                    ),
                ], className="charter-badges"),
            ], className="charter-header-content"),
            html.Div([
                html.Div([
                    html.Span("Approved by: ", className="charter-meta-label"),
                    html.Span(c.get("approved_by", "Pending"), className="charter-meta-value"),
                ]),
                html.Div([
                    html.Span("Date: ", className="charter-meta-label"),
                    html.Span(str(c.get("approved_date", "TBD")), className="charter-meta-value"),
                ]),
                html.Div([
                    html.Span("Budget: ", className="charter-meta-label"),
                    html.Span(c.get("budget", "TBD"), className="charter-meta-value"),
                ]),
                html.Div([
                    html.Span("Timeline: ", className="charter-meta-label"),
                    html.Span(c.get("timeline", "TBD"), className="charter-meta-value"),
                ]),
            ], className="charter-meta-row"),
        ], className="charter-card-header"),

        dbc.CardBody([
            # Two-column layout for charter sections
            dbc.Row([
                dbc.Col([
                    charter_section("Business Case", c.get("business_case", ""), "📋"),
                    charter_section("Objectives", 
                        html.Ul([
                            html.Li(obj.strip()) 
                            for obj in c.get("objectives", "").split("\n") 
                            if obj.strip()
                        ]),
                        "🎯"
                    ),
                    charter_section("Success Criteria", c.get("success_criteria", ""), "✅"),
                ], width=6),
                dbc.Col([
                    charter_section("Scope — In", c.get("scope_in", ""), "✓"),
                    charter_section("Scope — Out", c.get("scope_out", ""), "✗"),
                    charter_section("Stakeholders", c.get("stakeholders", ""), "👥"),
                    charter_section("Key Risks", c.get("risks", ""), "⚠️"),
                ], width=6),
            ]),
        ]),
    ], className="charter-card")


# ─── Charter Creation Form ──────────────────────────────────
def charter_form():
    return dbc.Card([
        dbc.CardHeader([
            html.H4("Create New Charter", className="mb-0"),
        ]),
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
                                 placeholder="1. Migrate 100% of tables by Q2\n2. Implement row-level security\n3. Enable lineage tracking"),
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
                    dbc.Textarea(id="charter-scope-in", rows=3,
                                 placeholder="What IS included in this project"),
                ], width=6),
                dbc.Col([
                    dbc.Label("Out of Scope"),
                    dbc.Textarea(id="charter-scope-out", rows=3,
                                 placeholder="What is explicitly NOT included"),
                ], width=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Key Stakeholders"),
                    dbc.Textarea(id="charter-stakeholders", rows=2,
                                 placeholder="CIO (Sponsor), VP Data (Owner), Finance Dir (Key User)"),
                ], width=6),
                dbc.Col([
                    dbc.Label("Known Risks"),
                    dbc.Textarea(id="charter-risks", rows=2,
                                 placeholder="Resource contention, scope changes, technical unknowns"),
                ], width=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Budget"),
                    dbc.Input(id="charter-budget", type="text", placeholder="$420,000"),
                ], width=3),
                dbc.Col([
                    dbc.Label("Timeline"),
                    dbc.Input(id="charter-timeline", type="text", placeholder="Jan 2026 — Aug 2026"),
                ], width=3),
                dbc.Col([
                    dbc.Label("Sponsor / Approver"),
                    dbc.Input(id="charter-approver", type="text", placeholder="VP Data & Analytics"),
                ], width=3),
                dbc.Col([
                    html.Br(),
                    dbc.Button("Create Charter", id="charter-submit", color="primary",
                               className="w-100 mt-1"),
                ], width=3),
            ]),
        ]),
    ], className="charter-form-card mb-4")


# ─── Page Layout ────────────────────────────────────────────
def layout():
    # Load sample charter for display
    charter_data = get_project_charter("prj-001")

    return html.Div([
        html.H4("Project Charters", className="page-title mb-3"),
        html.P(
            "Formal project authorization documents. Each charter defines the business case, "
            "scope, objectives, delivery method, and governance structure.",
            className="page-subtitle mb-4",
        ),

        # Tabs: View existing vs Create new
        dbc.Tabs([
            dbc.Tab(
                charter_display(charter_data),
                label="Unity Catalog Migration",
                tab_id="charter-uc",
            ),
            dbc.Tab(
                html.Div("Select a project to view its charter.", className="p-4 text-muted"),
                label="DLT Pipeline Framework",
                tab_id="charter-dlt",
            ),
            dbc.Tab(
                charter_form(),
                label="+ New Charter",
                tab_id="charter-new",
            ),
        ], id="charter-tabs", active_tab="charter-uc"),
    ])
