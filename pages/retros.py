"""
Retrospectives Page
====================
Sprint retrospective feedback organized by category with vote counts.
"""

import dash
from dash import html, callback, Input, Output
import dash_bootstrap_components as dbc
from services.auth_service import get_user_token
from services.sprint_service import get_sprints
from services.analytics_service import get_retro_items
from components.kpi_card import kpi_card
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from charts.theme import COLORS
from utils.labels import RETRO_LABELS

dash.register_page(__name__, path="/retros", name="Retrospectives")

CATEGORY_COLORS = {
    "went_well": COLORS["green"],
    "improve": COLORS["yellow"],
    "action": COLORS["accent"],
}
CATEGORY_ICONS = {
    "went_well": "hand-thumbs-up-fill",
    "improve": "arrow-up-circle-fill",
    "action": "lightning-charge-fill",
}


def _retro_card(item):
    """Render a single retro item card."""
    category = item.get("category", "improve")
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(
                    className=f"bi bi-{CATEGORY_ICONS.get(category, 'chat-fill')} me-2",
                    style={"color": CATEGORY_COLORS.get(category, COLORS["text_muted"])},
                ),
                html.Span(item.get("item_text", ""), className="small"),
            ]),
            html.Div([
                html.Span(
                    f"▲ {item.get('votes', 0)}",
                    className="small",
                    style={"color": COLORS["accent"]},
                ),
            ], className="mt-2"),
        ], className="p-2"),
    ], className="mb-2 bg-transparent border-secondary")


def _retro_column(category, items_df):
    """Render a retro category column."""
    cat_items = items_df[items_df["category"] == category] if not items_df.empty else items_df
    label = RETRO_LABELS.get(category, category.title())
    color = CATEGORY_COLORS.get(category, COLORS["text_muted"])
    count = len(cat_items)

    return dbc.Col([
        html.Div([
            html.I(
                className=f"bi bi-{CATEGORY_ICONS.get(category, 'chat-fill')} me-2",
                style={"color": color},
            ),
            html.Span(label, className="fw-bold", style={"color": color}),
            html.Span(f" ({count})", className="text-muted small"),
        ], className="mb-3 pb-2 border-bottom border-secondary"),
        html.Div([
            _retro_card(row.to_dict())
            for _, row in cat_items.iterrows()
        ] if not cat_items.empty else [
            empty_state("No items yet."),
        ]),
    ], width=4)


def _build_content():
    """Build the actual page content."""
    token = get_user_token()
    sprints = get_sprints("prj-001", user_token=token)

    # Get the most recent closed sprint for retro
    closed = sprints[sprints["status"] == "closed"] if not sprints.empty else sprints
    if not closed.empty:
        last_sprint = closed.iloc[-1]
        sprint_id = last_sprint["sprint_id"]
        sprint_name = last_sprint["name"]
    else:
        sprint_id = "sp-003"
        sprint_name = "Sprint 3"

    retro_items = get_retro_items(sprint_id, user_token=token)

    if not retro_items.empty:
        total = len(retro_items)
        total_votes = int(retro_items["votes"].sum())
        action_count = len(retro_items[retro_items["category"] == "action"])
    else:
        total = total_votes = action_count = 0

    return html.Div([
        html.H4("Retrospectives", className="page-title mb-1"),
        html.P(f"{sprint_name} Retrospective", className="page-subtitle mb-3",
               style={"color": COLORS["accent"]}),

        # KPI strip
        dbc.Row([
            dbc.Col(kpi_card("Total Items", total, "feedback items"), width=3),
            dbc.Col(kpi_card("Total Votes", total_votes, "team engagement"), width=3),
            dbc.Col(kpi_card("Action Items", action_count, "to follow up",
                             COLORS["accent"]), width=3),
            dbc.Col(kpi_card("Sprint", sprint_name, "retrospective"), width=3),
        ], className="kpi-strip mb-4"),

        # Three-column retro board
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    _retro_column(cat, retro_items)
                    for cat in ["went_well", "improve", "action"]
                ]),
            ]),
        ]),
    ])


def layout():
    return html.Div([
        html.Div(id="retros-content"),
        auto_refresh(interval_id="retros-refresh-interval"),
    ])


@callback(
    Output("retros-content", "children"),
    Input("retros-refresh-interval", "n_intervals"),
)
def refresh_retros(n):
    return _build_content()
