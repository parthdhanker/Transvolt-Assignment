from dash import html

NAV_ITEMS = [
    ("/dashboard", "Grid", "Dashboard"),
    ("/forecast", "TrendingUp", "Forecast Explorer"),
    ("/analytics", "BarChart3", "Analytics"),
    ("/insights", "Lightbulb", "Business Insights"),
]


def create_sidebar():
    return html.Nav(
        className="sidebar",
        children=[
            html.Div(
                className="sidebar-header",
                children=[
                    html.Div(
                        html.Span("DF", className="logo-icon"),
                        className="logo-wrapper",
                    ),
                    html.Div(
                        children=[
                            html.Span("Demand", className="logo-text-line1"),
                            html.Span("Forecast AI", className="logo-text-line2"),
                        ],
                        className="logo-text",
                    ),
                ],
            ),
            html.Div(
                className="sidebar-nav",
                children=[
                    html.A(
                        className=f"nav-item nav-{item[0].replace('/', '')}",
                        href=item[0],
                        children=[
                            html.Span(item[2]),
                        ],
                    )
                    for item in NAV_ITEMS
                ],
            ),
            html.Div(
                className="sidebar-footer",
                children=[
                    html.Div(
                        className="sidebar-about",
                        children=[
                            html.Span("v1.0.0", className="version-badge"),
                            html.Span("Data Science Portfolio", className="about-text"),
                        ],
                    ),
                ],
            ),
        ],
    )
