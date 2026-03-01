"""Tree walking utilities for inspecting Dash component structures."""

import dash_bootstrap_components as dbc
from dash import dcc, html


def _get_children(component):
    """Get the children of a Dash component as a list."""
    children = getattr(component, "children", None)
    if children is None:
        return []
    if isinstance(children, (list, tuple)):
        return list(children)
    return [children]


def find_all(component, component_type):
    """Recursively find all instances of a component type in the tree."""
    results = []
    if isinstance(component, component_type):
        results.append(component)
    for child in _get_children(component):
        if hasattr(child, "children") or hasattr(child, "className"):
            results.extend(find_all(child, component_type))
    return results


def find_rows_with_class(component, class_str):
    """Find all dbc.Row components whose className contains class_str."""
    rows = find_all(component, dbc.Row)
    return [r for r in rows if class_str in (getattr(r, "className", "") or "")]


def get_col_widths(row):
    """Extract width config from direct dbc.Col children of a Row.

    Returns a list of dicts with keys: width, md, lg, xl.
    Only includes keys that are explicitly set (not None).
    """
    cols = []
    for child in _get_children(row):
        if isinstance(child, dbc.Col):
            info = {}
            for attr in ("width", "md", "lg", "xl"):
                val = getattr(child, attr, None)
                if val is not None:
                    info[attr] = val
            cols.append(info)
    return cols


def find_cards_with_class(component, class_str):
    """Find all dbc.Card components whose className contains class_str."""
    cards = find_all(component, dbc.Card)
    return [c for c in cards if class_str in (getattr(c, "className", "") or "")]


def find_graphs(component):
    """Find all dcc.Graph instances in the tree."""
    return find_all(component, dcc.Graph)


def get_graph_heights(component):
    """Extract explicit heights from dcc.Graph style dicts.

    Returns list of (graph_id, height_str) tuples for graphs with explicit height.
    """
    graphs = find_graphs(component)
    results = []
    for g in graphs:
        style = getattr(g, "style", None) or {}
        if "height" in style:
            gid = getattr(g, "id", "unknown")
            results.append((gid, style["height"]))
    return results


def find_divs_with_class(component, class_str):
    """Find all html.Div components whose className contains class_str."""
    divs = find_all(component, html.Div)
    return [d for d in divs if class_str in (getattr(d, "className", "") or "")]


def find_inline_font_sizes(component, min_px=11):
    """Find components with inline fontSize below min_px threshold.

    Returns list of (component_type, fontSize_value) tuples.
    """
    results = []
    style = getattr(component, "style", None) or {}
    font_size = style.get("fontSize") or style.get("font-size")
    if font_size is not None:
        px_val = _parse_px(font_size)
        if px_val is not None and px_val < min_px:
            results.append((type(component).__name__, font_size))

    for child in _get_children(component):
        if hasattr(child, "children") or hasattr(child, "style"):
            results.extend(find_inline_font_sizes(child, min_px))
    return results


def _parse_px(value):
    """Parse a pixel value like '12px' or 12 into a number. Returns None if not parseable."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and value.endswith("px"):
        try:
            return float(value[:-2])
        except ValueError:
            return None
    return None
