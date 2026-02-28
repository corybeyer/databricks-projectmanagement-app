"""KPI Card — reusable metric display component."""

from dash import html
import dash_bootstrap_components as dbc


def kpi_card(label, value, sub_text, sub_color=None, icon=None, icon_color=None):
    body_children = []
    if icon:
        color_class = f"icon-{icon_color}" if icon_color else "icon-blue"
        body_children.append(
            html.Div(
                html.I(className=f"bi bi-{icon}"),
                className=f"kpi-icon-wrapper {color_class}",
            )
        )
    body_children.extend([
        html.Div(label, className="kpi-label"),
        html.Div(str(value), className="kpi-value",
                 style={"color": sub_color} if sub_color else {}),
        html.Div(sub_text, className="kpi-sub",
                 style={"color": sub_color} if sub_color else {}),
    ])
    return dbc.Card(
        dbc.CardBody(body_children),
        className="kpi-card",
    )
