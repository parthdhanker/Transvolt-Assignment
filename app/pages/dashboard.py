import dash
from dash import html
from app.services.data_service import get_stats
from app.services.insights_service import compute_insights
from app.components.kpi_card import create_kpi_card

dash.register_page(__name__, path="/dashboard")

COLORS = {
    "indigo": "#4F46E5",
    "green": "#10B981",
    "amber": "#F59E0B",
    "red": "#EF4444",
}


def layout():
    stats = get_stats()
    insights = compute_insights()

    return html.Div(
        className="page-content",
        children=[
            html.Div(
                className="page-header",
                children=[
                    html.H1("Dashboard", className="page-title"),
                    html.P("Demand forecasting overview for all SKUs and supermarkets", className="page-desc"),
                ],
            ),
            html.Div(
                className="kpi-grid",
                children=[
                    create_kpi_card("Supermarkets", stats["total_supermarkets"], "3 chains", color=COLORS["indigo"]),
                    create_kpi_card("SKUs", stats["total_skus"], "3 products", color=COLORS["green"]),
                    create_kpi_card("Total Demand", f"{stats['total_records']:,}", "units sold", color=COLORS["amber"]),
                    create_kpi_card("Date Range", f"{stats['date_min']}", f"to {stats['date_max']}", color=COLORS["red"]),
                    create_kpi_card("Avg Weekly", f"{insights['average_weekly_demand']:,.0f}", "units/week", color=COLORS["indigo"]),
                    create_kpi_card("Forecast Horizon", "8 Weeks", "Direct multi-step", color=COLORS["green"]),
                ],
            ),
            html.Div(
                className="card",
                children=[
                    html.H2("Top Performing Series", className="card-title"),
                    html.Div(
                        className="series-stats-grid",
                        id="series-stats",
                        children=[
                            html.Div(
                                className="series-stat-item",
                                children=[
                                    html.Span(label, className="series-stat-label"),
                                    html.Span(f"{value:,.0f}", className="series-stat-value"),
                                    html.Div(
                                        className="stat-bar",
                                        children=[
                                            html.Div(
                                                className="stat-bar-fill",
                                                style={"width": f"{min(value / max_val * 100, 100):.0f}%"},
                                            )
                                        ],
                                    ),
                                ],
                            )
                            for label, value in
                            sorted(insights["mean_by_sku_market"].items(), key=lambda x: -x[1])
                            for max_val in [max(insights["mean_by_sku_market"].values()) or 1]
                        ],
                    ),
                ],
            ),
        ],
    )



