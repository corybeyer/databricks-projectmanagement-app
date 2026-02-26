"""Charter Display — renders a project charter document."""

from dash import html
import dash_bootstrap_components as dbc
from charts.theme import COLORS


def charter_section(title, content, icon=""):
    return html.Div([
        html.Div([
            html.Span(icon + " " if icon else ""),
            html.Span(title, className="charter-section-title"),
        ], className="charter-section-header"),
        html.Div(content, className="charter-section-body"),
    ], className="charter-section")


def charter_display(charter):
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
        dbc.CardHeader([
            html.Div([
                html.H3(c.get("project_name", "Project Charter"), className="charter-title"),
                html.Div([
                    html.Span(
                        c.get("delivery_method", "Hybrid"),
                        className="method-badge",
                        style={"backgroundColor": f"{method_color}20", "color": method_color},
                    ),
                    html.Span(f"v{c.get('version', 1)}", className="version-badge"),
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
            dbc.Row([
                dbc.Col([
                    charter_section("Business Case", c.get("business_case", ""), "📋"),
                    charter_section("Objectives",
                        html.Ul([
                            html.Li(obj.strip())
                            for obj in c.get("objectives", "").split("\n")
                            if obj.strip()
                        ]), "🎯"),
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
