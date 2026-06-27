from dash import html


def create_kpi_card(title, value, subtitle=None, icon=None, color=None):
    style = {}
    if color:
        style["borderTop"] = f"3px solid {color}"

    return html.Div(
        className="kpi-card",
        style=style,
        children=[
            html.Div(
                className="kpi-header",
                children=[
                    html.Span(title, className="kpi-title"),
                ],
            ),
            html.Div(
                className="kpi-value-wrapper",
                children=[
                    html.Span(str(value), className="kpi-value"),
                ],
            ),
            html.Div(
                className="kpi-footer",
                children=[
                    html.Span(subtitle or "", className="kpi-subtitle"),
                ],
            ),
        ],
    )
