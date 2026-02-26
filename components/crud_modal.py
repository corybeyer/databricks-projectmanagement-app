"""
CRUD Modal Component System
============================
Reusable modal and form builder for all Phase 2 CRUD operations.

Provides factory functions that generate Dash Bootstrap modals from
declarative field definitions. Pages define their field lists once,
then use these helpers to build the modal UI and wire up callbacks
with consistent ID patterns and validation feedback.

Public API:
    crud_modal(id_prefix, title, fields, size)  — build a form modal
    confirm_delete_modal(id_prefix, entity_name) — build a delete confirmation
    get_modal_values(id_prefix, field_defs, *args) — extract form values
    set_field_errors(id_prefix, field_defs, errors) — build validation outputs
    modal_field_states(id_prefix, field_defs) — State() list for callbacks
    modal_error_outputs(id_prefix, field_defs) — Output() list for validation

ID Convention:
    All component IDs are prefixed with ``id_prefix`` to avoid collisions
    when multiple modals exist on the same page (e.g., "sprint-task-modal",
    "risk-modal"). Pages choose the prefix; this module never hardcodes one.

FieldDef format:
    {
        "id": "title",           # Field ID (auto-prefixed)
        "label": "Title",        # Display label
        "type": "text",          # text | select | textarea | number | date
        "required": True,        # Show required indicator (*)
        "placeholder": "...",    # Optional placeholder
        "options": [...],        # For select: [{"label": "...", "value": "..."}]
        "min": 1, "max": 5,      # For number type
        "rows": 3,               # For textarea (default 3)
    }
"""

from typing import List, Optional

from dash import dcc, html
import dash_bootstrap_components as dbc


# ── Public Functions ─────────────────────────────────────────────────


def crud_modal(
    id_prefix: str,
    title: str,
    fields: List[dict],
    size: str = "lg",
) -> dbc.Modal:
    """Build a reusable CRUD modal with a form built from field definitions.

    Args:
        id_prefix: Page-specific prefix for all component IDs (e.g. "sprint-task").
        title: Modal title text (e.g. "Create Task", "Edit Risk").
        fields: List of FieldDef dicts — see module docstring for format.
        size: Bootstrap modal size — ``"sm"``, ``"lg"``, or ``"xl"`` (default ``"lg"``).

    Returns:
        A ``dbc.Modal`` with ``id=f"{id_prefix}-modal"``, containing a form
        with labelled inputs, cancel/save buttons, and per-field feedback.
    """
    form_rows = [_build_form_row(id_prefix, field) for field in fields]

    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle(title, id=f"{id_prefix}-modal-title")),
            dbc.ModalBody(dbc.Form(form_rows, id=f"{id_prefix}-form")),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Cancel",
                        id=f"{id_prefix}-cancel-btn",
                        color="secondary",
                        outline=True,
                    ),
                    dbc.Button(
                        "Save",
                        id=f"{id_prefix}-save-btn",
                        color="primary",
                    ),
                ]
            ),
        ],
        id=f"{id_prefix}-modal",
        size=size,
        is_open=False,
        centered=True,
        backdrop="static",
    )


def confirm_delete_modal(
    id_prefix: str,
    entity_name: str = "item",
) -> html.Div:
    """Build a delete-confirmation modal with a hidden store for the target ID.

    Args:
        id_prefix: Page-specific prefix (e.g. "sprint-task").
        entity_name: Human-readable entity name (e.g. "task", "risk").

    Returns:
        An ``html.Div`` containing the confirmation ``dbc.Modal``
        (``id=f"{id_prefix}-delete-modal"``) and a ``dcc.Store``
        (``id=f"{id_prefix}-delete-target-store"``) that holds the ID
        of the item pending deletion.
    """
    modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Confirm Delete")),
            dbc.ModalBody(
                f"Are you sure you want to delete this {entity_name}? "
                "This action can be undone by an administrator."
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Cancel",
                        id=f"{id_prefix}-delete-cancel-btn",
                        color="secondary",
                        outline=True,
                    ),
                    dbc.Button(
                        "Delete",
                        id=f"{id_prefix}-delete-confirm-btn",
                        color="danger",
                    ),
                ]
            ),
        ],
        id=f"{id_prefix}-delete-modal",
        is_open=False,
        centered=True,
    )

    store = dcc.Store(id=f"{id_prefix}-delete-target-store", data=None)

    return html.Div([modal, store])


def get_modal_values(
    id_prefix: str,
    field_defs: List[dict],
    *args,
) -> dict:
    """Extract form values from callback ``State`` arguments into a dict.

    Usage in a callback::

        @callback(
            ...,
            [State(f"{prefix}-{f['id']}", "value") for f in FIELDS],
        )
        def save(n_clicks, *field_values):
            data = get_modal_values(prefix, FIELDS, *field_values)
            # data = {"title": "...", "priority": "high", ...}

    Args:
        id_prefix: Same prefix used when building the modal.
        field_defs: Same field definition list used in ``crud_modal()``.
        *args: Positional values in the same order as ``field_defs``.

    Returns:
        Dict mapping each field's ``id`` to its current value.
    """
    result = {}
    for i, field in enumerate(field_defs):
        if i < len(args):
            result[field["id"]] = args[i]
    return result


def set_field_errors(
    id_prefix: str,
    field_defs: List[dict],
    errors: dict,
) -> tuple:
    """Generate validation-feedback values for every field.

    Args:
        id_prefix: Same prefix used when building the modal.
        field_defs: Same field definition list used in ``crud_modal()``.
        errors: Dict of ``{field_id: error_message}`` for fields with errors.
            Fields not present in this dict are marked as valid.

    Returns:
        ``(is_invalid_list, feedback_list)`` where each list has one entry
        per field in ``field_defs``:

        - ``is_invalid_list``: ``bool`` for each field's ``invalid`` prop.
        - ``feedback_list``: ``str`` for each field's ``FormFeedback.children``.

    Usage::

        invalids, feedbacks = set_field_errors(prefix, FIELDS, {"title": "Required"})
        # Flatten and return as callback outputs via modal_error_outputs()
    """
    is_invalid: List[bool] = []
    feedback: List[str] = []
    for field in field_defs:
        field_id = field["id"]
        if field_id in errors:
            is_invalid.append(True)
            feedback.append(errors[field_id])
        else:
            is_invalid.append(False)
            feedback.append("")
    return is_invalid, feedback


def modal_field_states(id_prefix: str, field_defs: List[dict]) -> list:
    """Generate a ``State(...)`` list for all modal fields.

    Convenience function for use in ``@callback`` decorators::

        @callback(
            ...,
            modal_field_states("sprint-task", TASK_FIELDS),
        )
        def save(n_clicks, *field_values):
            ...

    Returns:
        List of ``State(f"{id_prefix}-{field['id']}", "value")`` objects.
    """
    from dash import State

    return [State(f"{id_prefix}-{field['id']}", "value") for field in field_defs]


def modal_error_outputs(id_prefix: str, field_defs: List[dict]) -> list:
    """Generate an ``Output(...)`` list for field validation feedback.

    Returns two outputs per field (``invalid`` prop and ``FormFeedback.children``),
    interleaved so the callback can return a flat list::

        @callback(
            [Output(..., "is_open"), *modal_error_outputs(prefix, FIELDS)],
            ...
        )
        def save(...):
            invalids, feedbacks = set_field_errors(prefix, FIELDS, errors)
            # Interleave: [invalid_0, feedback_0, invalid_1, feedback_1, ...]
            error_outputs = []
            for inv, fb in zip(invalids, feedbacks):
                error_outputs.extend([inv, fb])
            return [False, *error_outputs]

    Returns:
        List of ``Output`` objects — two per field (``invalid``, ``children``).
    """
    from dash import Output

    outputs: list = []
    for field in field_defs:
        outputs.append(Output(f"{id_prefix}-{field['id']}", "invalid"))
        outputs.append(Output(f"{id_prefix}-{field['id']}-feedback", "children"))
    return outputs


# ── Internal Helpers ─────────────────────────────────────────────────


def _build_form_row(id_prefix: str, field: dict) -> dbc.Row:
    """Build a single labelled form row with input and feedback."""
    label_text = field["label"]
    if field.get("required"):
        label_text += " *"

    input_component = _build_field_input(id_prefix, field)
    feedback = dbc.FormFeedback(
        id=f"{id_prefix}-{field['id']}-feedback",
        type="invalid",
    )

    return dbc.Row(
        [
            dbc.Label(label_text, width=3),
            dbc.Col([input_component, feedback], width=9),
        ],
        className="mb-3",
    )


def _build_field_input(id_prefix: str, field: dict):
    """Return the appropriate input component for a field definition."""
    field_type = field.get("type", "text")
    field_id = f"{id_prefix}-{field['id']}"
    placeholder = field.get("placeholder", "")

    if field_type == "text":
        return dbc.Input(
            id=field_id,
            type="text",
            placeholder=placeholder,
        )

    if field_type == "number":
        return dbc.Input(
            id=field_id,
            type="number",
            placeholder=placeholder,
            min=field.get("min"),
            max=field.get("max"),
        )

    if field_type == "date":
        return dbc.Input(
            id=field_id,
            type="date",
        )

    if field_type == "select":
        options = field.get("options", [])
        return dbc.Select(
            id=field_id,
            options=options,
            placeholder=placeholder or "Select...",
        )

    if field_type == "textarea":
        rows = field.get("rows", 3)
        return dbc.Textarea(
            id=field_id,
            placeholder=placeholder,
            rows=rows,
        )

    # Fallback: treat unknown types as text
    return dbc.Input(
        id=field_id,
        type="text",
        placeholder=placeholder,
    )
