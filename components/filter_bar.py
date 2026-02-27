"""Filter Bar — reusable filter controls for data-heavy pages."""

from dash import html, dcc
import dash_bootstrap_components as dbc


def filter_bar(page_prefix, filters):
    """Build a filter bar row from filter definitions.

    Each filter dict:
        {"id": str, "label": str, "type": "select"|"date_range"|"text",
         "options": list, "multi": bool}
    """
    cols = []
    for f in filters:
        fid = f"{page_prefix}-{f['id']}-filter"
        label = f["label"]

        if f.get("type") == "select":
            control = dcc.Dropdown(
                id=fid,
                options=f.get("options", []),
                multi=f.get("multi", True),
                placeholder=f"All {label}",
                clearable=True,
                className="filter-dropdown",
            )
        elif f.get("type") == "date_range":
            control = dcc.DatePickerRange(
                id=fid,
                className="filter-date-range",
            )
        elif f.get("type") == "text":
            control = dbc.Input(
                id=fid,
                type="text",
                placeholder=f"Search {label.lower()}...",
                size="sm",
                debounce=True,
            )
        else:
            continue

        cols.append(
            dbc.Col([
                html.Small(label, className="text-muted d-block mb-1"),
                control,
            ], width=f.get("width", True), className="mb-2")
        )

    if not cols:
        return html.Div()

    return dbc.Row(cols, className="filter-bar mb-3 align-items-end")


def sort_toggle(page_prefix, options):
    """Build a sort dropdown.

    options: list of {"label": str, "value": str}
    """
    return html.Div([
        html.Small("Sort by", className="text-muted me-2",
                   style={"whiteSpace": "nowrap"}),
        dcc.Dropdown(
            id=f"{page_prefix}-sort-toggle",
            options=options,
            value=options[0]["value"] if options else None,
            clearable=False,
            style={"minWidth": "150px"},
            className="filter-dropdown",
        ),
    ], className="d-flex align-items-center mb-3")
