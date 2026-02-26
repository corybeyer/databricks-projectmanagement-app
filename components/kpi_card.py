"""KPI Card — reusable metric display component."""

from dash import html
import dash_bootstrap_components as dbc


def kpi_card(label, value, sub_text, sub_color=None):
    return dbc.Card(
        dbc.CardBody([
            html.Div(label, className="kpi-label"),
            html.Div(str(value), className="kpi-value",
                     style={"color": sub_color} if sub_color else {}),
            html.Div(sub_text, className="kpi-sub",
                     style={"color": sub_color} if sub_color else {}),
        ]),
        className="kpi-card",
    )
