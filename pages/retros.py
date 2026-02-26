"""
Retrospectives Page -- CRUD + Voting
=====================================
Sprint retrospective board with three-column layout (went_well, improve, action_item),
voting, create/edit/delete CRUD, and convert-to-task for action items.
"""

import json
import dash
from dash import html, dcc, callback, Input, Output, State, ctx, ALL, no_update
import dash_bootstrap_components as dbc
from services.auth_service import get_user_token, get_user_email
from services import retro_service
from services.sprint_service import get_sprints
from components.kpi_card import kpi_card
from components.empty_state import empty_state
from components.auto_refresh import auto_refresh
from components.crud_modal import (
    crud_modal, confirm_delete_modal, get_modal_values,
    set_field_errors, modal_field_states, modal_error_outputs,
)
from charts.theme import COLORS
from utils.labels import RETRO_LABELS

dash.register_page(__name__, path="/retros", name="Retrospectives")

# -- Category display config --------------------------------------

CATEGORY_COLORS = {
    "went_well": COLORS["green"],
    "improve": COLORS["yellow"],
    "action_item": COLORS["accent"],
    "action": COLORS["accent"],
}
CATEGORY_ICONS = {
    "went_well": "hand-thumbs-up-fill",
    "improve": "arrow-up-circle-fill",
    "action_item": "lightning-charge-fill",
    "action": "lightning-charge-fill",
}

# The three board columns -- action_item is the canonical category
BOARD_CATEGORIES = ["went_well", "improve", "action_item"]

# -- CRUD Modal Field Definitions ---------------------------------

RETRO_FIELDS = [
    {"id": "category", "label": "Category", "type": "select", "required": True,
     "options": [
         {"label": "Went Well", "value": "went_well"},
         {"label": "To Improve", "value": "improve"},
         {"label": "Action Item", "value": "action_item"},
     ]},
    {"id": "body", "label": "Description", "type": "textarea", "required": True,
     "rows": 4, "placeholder": "What happened?"},
]

# -- Status display -----------------------------------------------

STATUS_BADGE_COLORS = {
    "open": "info",
    "converted": "success",
}


# -- Helper functions ---------------------------------------------


def _retro_card(item):
    """Render a single retro item card with vote/edit/delete/convert buttons."""
    category = item.get("category", "improve")
    retro_id = item.get("retro_id", "")
    votes = item.get("votes", 0)
    status = item.get("status", "open")
    body_text = item.get("body", "") or item.get("item_text", "")

    # Action buttons
    action_buttons = [
        dbc.Button(
            [html.I(className="bi bi-arrow-up-circle me-1"),
             html.Span(str(votes), className="small")],
            id={"type": "retros-retro-vote-btn", "index": retro_id},
            size="sm", color="link", className="p-0 me-2",
            style={"color": COLORS["accent"]},
        ),
        dbc.Button(
            html.I(className="bi bi-pencil-square"),
            id={"type": "retros-retro-edit-btn", "index": retro_id},
            size="sm", color="link", className="p-0 me-2 text-muted",
        ),
        dbc.Button(
            html.I(className="bi bi-trash"),
            id={"type": "retros-retro-delete-btn", "index": retro_id},
            size="sm", color="link", className="p-0 me-2 text-muted",
        ),
    ]

    # Convert-to-task button for action items that aren't converted yet
    if category in ("action", "action_item") and status != "converted":
        action_buttons.append(
            dbc.Button(
                [html.I(className="bi bi-arrow-right-circle me-1"),
                 html.Span("Convert", className="small")],
                id={"type": "retros-retro-convert-btn", "index": retro_id},
                size="sm", color="link", className="p-0",
                style={"color": COLORS["green"]},
            ),
        )

    # Converted badge
    status_badge = None
    if status == "converted":
        status_badge = dbc.Badge("Converted", color="success", className="ms-2 small")

    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(
                    className=f"bi bi-{CATEGORY_ICONS.get(category, 'chat-fill')} me-2",
                    style={"color": CATEGORY_COLORS.get(category, COLORS["text_muted"])},
                ),
                html.Span(body_text, className="small"),
                status_badge,
            ]),
            html.Div(
                action_buttons,
                className="mt-2 d-flex align-items-center",
            ),
        ], className="p-2"),
    ], className="mb-2 bg-transparent border-secondary")


def _retro_column(category, items_df):
    """Render a retro category column."""
    # For the action_item column, also include legacy "action" category
    if category == "action_item":
        cat_items = items_df[items_df["category"].isin(["action", "action_item"])] if not items_df.empty else items_df
    else:
        cat_items = items_df[items_df["category"] == category] if not items_df.empty else items_df

    label = RETRO_LABELS.get(category, category.replace("_", " ").title())
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


def _build_content(sprint_id=None):
    """Build the actual page content."""
    token = get_user_token()
    sprints = get_sprints("prj-001", user_token=token)

    # Determine which sprint to show
    if sprint_id and not sprints.empty:
        match = sprints[sprints["sprint_id"] == sprint_id]
        if not match.empty:
            sprint_name = match.iloc[0]["name"]
        else:
            sprint_name = sprint_id
    else:
        # Default to most recent closed sprint
        closed = sprints[sprints["status"] == "closed"] if not sprints.empty else sprints
        if not closed.empty:
            last_sprint = closed.iloc[-1]
            sprint_id = last_sprint["sprint_id"]
            sprint_name = last_sprint["name"]
        elif not sprints.empty:
            sprint_id = sprints.iloc[0]["sprint_id"]
            sprint_name = sprints.iloc[0]["name"]
        else:
            sprint_id = "sp-003"
            sprint_name = "Sprint 3"

    retro_items = retro_service.get_retro_items(sprint_id, user_token=token)

    # Filter to this sprint in sample data mode (sample returns all)
    if not retro_items.empty and "sprint_id" in retro_items.columns:
        retro_items = retro_items[retro_items["sprint_id"] == sprint_id]

    # Filter out deleted
    if not retro_items.empty and "is_deleted" in retro_items.columns:
        retro_items = retro_items[retro_items["is_deleted"] == False]  # noqa: E712

    # Sort by votes DESC
    if not retro_items.empty and "votes" in retro_items.columns:
        retro_items = retro_items.sort_values("votes", ascending=False)

    # Calculate KPIs
    if not retro_items.empty:
        total = len(retro_items)
        total_votes = int(retro_items["votes"].sum())
        action_count = len(retro_items[retro_items["category"].isin(["action", "action_item"])])
        converted_count = len(
            retro_items[retro_items["status"] == "converted"]
        ) if "status" in retro_items.columns else 0
    else:
        total = total_votes = action_count = converted_count = 0

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
            dbc.Col(kpi_card("Converted", converted_count, "to tasks",
                             COLORS["green"] if converted_count > 0 else None), width=3),
        ], className="kpi-strip mb-4"),

        # Three-column retro board
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    _retro_column(cat, retro_items)
                    for cat in BOARD_CATEGORIES
                ]),
            ]),
        ]),
    ])


# -- Layout ----------------------------------------------------------


def layout():
    return html.Div([
        # Stores
        dcc.Store(id="retros-mutation-counter", data=0),
        dcc.Store(id="retros-selected-retro-store", data=None),
        dcc.Store(id="retros-selected-sprint-store", data=None),

        # Sprint selector + toolbar
        dbc.Row([
            dbc.Col([
                dbc.Select(
                    id="retros-sprint-selector",
                    placeholder="Select sprint...",
                ),
            ], width=4),
            dbc.Col([
                dbc.Button(
                    [html.I(className="bi bi-plus-circle me-1"), "Add Item"],
                    id="retros-add-retro-btn", color="primary", size="sm",
                ),
            ], width=8, className="d-flex align-items-start justify-content-end"),
        ], className="mb-3"),

        # Content area
        html.Div(id="retros-content"),
        auto_refresh(interval_id="retros-refresh-interval"),

        # Modals
        crud_modal("retros-retro", "Create Retro Item", RETRO_FIELDS, size="lg"),
        confirm_delete_modal("retros-retro", "retro item"),
    ])


# -- Callbacks -------------------------------------------------------


@callback(
    Output("retros-sprint-selector", "options"),
    Output("retros-sprint-selector", "value"),
    Input("retros-refresh-interval", "n_intervals"),
)
def populate_sprint_selector(n):
    """Populate the sprint selector dropdown."""
    token = get_user_token()
    sprints = get_sprints("prj-001", user_token=token)

    if sprints.empty:
        return [], None

    options = [
        {"label": f"{row['name']} ({row['status']})", "value": row["sprint_id"]}
        for _, row in sprints.iterrows()
    ]

    # Default to most recent closed sprint
    closed = sprints[sprints["status"] == "closed"]
    if not closed.empty:
        default_val = closed.iloc[-1]["sprint_id"]
    else:
        default_val = sprints.iloc[0]["sprint_id"]

    return options, default_val


@callback(
    Output("retros-content", "children"),
    Input("retros-refresh-interval", "n_intervals"),
    Input("retros-mutation-counter", "data"),
    Input("retros-sprint-selector", "value"),
)
def refresh_retros(n, mutation_count, sprint_id):
    """Refresh retro content on interval, mutation, or sprint change."""
    return _build_content(sprint_id=sprint_id)


@callback(
    Output("retros-retro-modal", "is_open", allow_duplicate=True),
    Output("retros-retro-modal-title", "children", allow_duplicate=True),
    Output("retros-selected-retro-store", "data", allow_duplicate=True),
    Output("retros-retro-category", "value", allow_duplicate=True),
    Output("retros-retro-body", "value", allow_duplicate=True),
    Input("retros-add-retro-btn", "n_clicks"),
    Input({"type": "retros-retro-edit-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def toggle_retro_modal(add_clicks, edit_clicks):
    """Open retro modal for create (blank) or edit (populated)."""
    triggered = ctx.triggered_id

    # Create mode
    if triggered == "retros-add-retro-btn":
        return True, "Create Retro Item", None, None, ""

    # Edit mode -- pattern-match button
    if isinstance(triggered, dict) and triggered.get("type") == "retros-retro-edit-btn":
        retro_id = triggered["index"]
        token = get_user_token()
        item_df = retro_service.get_retro_item(retro_id, user_token=token)

        # In sample data mode, filter to the specific item
        if not item_df.empty and "retro_id" in item_df.columns:
            item_df = item_df[item_df["retro_id"] == retro_id]

        if item_df.empty:
            return (no_update,) * 5
        item = item_df.iloc[0]
        stored = {"retro_id": retro_id, "updated_at": str(item.get("updated_at", ""))}
        return (
            True, f"Edit Retro Item -- {retro_id}",
            json.dumps(stored),
            item.get("category"),
            item.get("body", "") or item.get("item_text", ""),
        )

    return (no_update,) * 5


@callback(
    Output("retros-retro-modal", "is_open", allow_duplicate=True),
    Output("retros-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    *modal_error_outputs("retros-retro", RETRO_FIELDS),
    Input("retros-retro-save-btn", "n_clicks"),
    State("retros-selected-retro-store", "data"),
    State("retros-mutation-counter", "data"),
    State("retros-sprint-selector", "value"),
    *modal_field_states("retros-retro", RETRO_FIELDS),
    prevent_initial_call=True,
)
def save_retro_item(n_clicks, stored_retro, counter, sprint_id, *field_values):
    """Save (create or update) a retro item."""
    form_data = get_modal_values("retros-retro", RETRO_FIELDS, *field_values)
    form_data["sprint_id"] = sprint_id or "sp-003"

    token = get_user_token()
    email = get_user_email()

    if stored_retro:
        stored = json.loads(stored_retro) if isinstance(stored_retro, str) else stored_retro
        retro_id = stored["retro_id"]
        expected = stored.get("updated_at", "")
        result = retro_service.update_retro_item_from_form(
            retro_id, form_data, expected,
            user_email=email, user_token=token,
        )
    else:
        result = retro_service.create_retro_item_from_form(
            form_data, user_email=email, user_token=token,
        )

    if result["success"]:
        no_errors = set_field_errors("retros-retro", RETRO_FIELDS, {})
        error_outputs = []
        for inv, fb in zip(no_errors[0], no_errors[1]):
            error_outputs.extend([inv, fb])
        return (False, (counter or 0) + 1, result["message"], "Success", "success", True,
                *error_outputs)

    errors = result.get("errors", {})
    field_errors = set_field_errors("retros-retro", RETRO_FIELDS, errors)
    error_outputs = []
    for inv, fb in zip(field_errors[0], field_errors[1]):
        error_outputs.extend([inv, fb])
    return (True, no_update, result["message"], "Error", "danger", True,
            *error_outputs)


@callback(
    Output("retros-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input({"type": "retros-retro-vote-btn", "index": ALL}, "n_clicks"),
    State("retros-mutation-counter", "data"),
    prevent_initial_call=True,
)
def vote_retro_action(n_clicks_list, counter):
    """Upvote a retro item."""
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        return (no_update,) * 5

    retro_id = triggered["index"]
    token = get_user_token()
    email = get_user_email()

    result = retro_service.vote_retro_item(retro_id, user_email=email, user_token=token)
    if result["success"]:
        return (counter or 0) + 1, result["message"], "Voted", "success", True
    return no_update, result["message"], "Error", "danger", True


@callback(
    Output("retros-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input({"type": "retros-retro-convert-btn", "index": ALL}, "n_clicks"),
    State("retros-mutation-counter", "data"),
    prevent_initial_call=True,
)
def convert_to_task_action(n_clicks_list, counter):
    """Convert an action item retro item to a task."""
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        return (no_update,) * 5

    retro_id = triggered["index"]
    token = get_user_token()
    email = get_user_email()

    result = retro_service.convert_to_task(retro_id, user_email=email, user_token=token)
    if result["success"]:
        return (counter or 0) + 1, result["message"], "Converted", "success", True
    return no_update, result["message"], "Error", "danger", True


@callback(
    Output("retros-retro-delete-modal", "is_open", allow_duplicate=True),
    Output("retros-retro-delete-target-store", "data", allow_duplicate=True),
    Input({"type": "retros-retro-delete-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_delete_modal(n_clicks_list):
    """Open delete confirmation with the retro item ID."""
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        return no_update, no_update
    retro_id = triggered["index"]
    return True, retro_id


@callback(
    Output("retros-retro-delete-modal", "is_open", allow_duplicate=True),
    Output("retros-mutation-counter", "data", allow_duplicate=True),
    Output("toast-message", "children", allow_duplicate=True),
    Output("toast-message", "header", allow_duplicate=True),
    Output("toast-message", "icon", allow_duplicate=True),
    Output("toast-message", "is_open", allow_duplicate=True),
    Input("retros-retro-delete-confirm-btn", "n_clicks"),
    State("retros-retro-delete-target-store", "data"),
    State("retros-mutation-counter", "data"),
    prevent_initial_call=True,
)
def confirm_delete_retro(n_clicks, retro_id, counter):
    """Soft-delete the retro item."""
    if not retro_id:
        return no_update, no_update, no_update, no_update, no_update, no_update

    token = get_user_token()
    email = get_user_email()
    success = retro_service.delete_retro_item(retro_id, user_email=email, user_token=token)

    if success:
        return False, (counter or 0) + 1, "Retro item deleted", "Deleted", "success", True
    return False, no_update, "Failed to delete retro item", "Error", "danger", True


@callback(
    Output("retros-retro-modal", "is_open", allow_duplicate=True),
    Input("retros-retro-cancel-btn", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_retro_modal(n):
    """Close retro modal on cancel."""
    return False
