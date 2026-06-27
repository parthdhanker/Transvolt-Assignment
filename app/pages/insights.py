import dash
from dash import html, dcc
from app.services.insights_service import compute_insights

dash.register_page(__name__, path="/insights")

MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}


def layout():
    insights = compute_insights()

    peak_text = "; ".join(
        f"{sku}: {MONTH_NAMES.get(m, m)}"
        for sku, m in insights["peak_months"].items()
    )
    trough_text = "; ".join(
        f"{sku}: {MONTH_NAMES.get(m, m)}"
        for sku, m in insights["trough_months"].items()
    )
    trend_text = "; ".join(
        f"{sku} ({dir})"
        for sku, dir in insights["trend_direction"].items()
    )

    series_stats = sorted(
        insights["mean_by_sku_market"].items(),
        key=lambda x: -x[1],
    )

    return html.Div(
        className="page-content",
        children=[
            html.Div(
                className="page-header",
                children=[
                    html.H1("Business Insights", className="page-title"),
                    html.P("Automatically computed insights from demand data and forecasts", className="page-desc"),
                ],
            ),
            html.Div(
                className="insights-grid",
                children=[
                    _insight_card(
                        "Highest Demand SKU",
                        insights["highest_demand_sku"],
                        f"{insights['highest_demand_sku_value']:,.0f} units total",
                        "#4F46E5",
                    ),
                    _insight_card(
                        "Highest Demand Market",
                        insights["highest_demand_market"],
                        f"{insights['highest_demand_market_value']:,.0f} units total",
                        "#10B981",
                    ),
                    _insight_card(
                        "Average Weekly Demand",
                        f"{insights['average_weekly_demand']:,.0f}",
                        f"Median: {insights['median_weekly_demand']:,.0f}",
                        "#F59E0B",
                    ),
                    _insight_card(
                        "Promotion Uplift",
                        f"+{insights['promotion_uplift_pct']:.1f}%",
                        f"{insights['promo_weeks_count']} promo weeks out of {insights['total_weeks']} total",
                        "#EF4444",
                    ),
                    _insight_card(
                        "Data Coverage",
                        insights["date_range"],
                        f"{insights['num_series']} SKU x Market series",
                        "#6366F1",
                    ),
                    _insight_card(
                        "Total Demand",
                        f"{insights['total_demand']:,.0f}",
                        "units across all series",
                        "#8B5CF6",
                    ),
                ],
            ),
            html.Div(
                className="card-grid-2",
                children=[
                    html.Div(
                        className="card",
                        children=[
                            html.H2("Seasonality Peaks & Troughs", className="card-title"),
                            html.Div(
                                className="insight-section",
                                children=[
                                    html.Div(
                                        className="insight-subsection",
                                        children=[
                                            html.Span("Peak Months", className="insight-subtitle"),
                                            html.P(peak_text, className="insight-text"),
                                        ],
                                    ),
                                    html.Div(
                                        className="insight-subsection",
                                        children=[
                                            html.Span("Trough Months", className="insight-subtitle"),
                                            html.P(trough_text, className="insight-text"),
                                        ],
                                    ),
                                    html.Div(
                                        className="insight-subsection",
                                        children=[
                                            html.Span("Trend Direction", className="insight-subtitle"),
                                            html.P(trend_text, className="insight-text"),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        className="card",
                        children=[
                            html.H2("Series Rankings (Mean Weekly Demand)", className="card-title"),
                            html.Div(
                                className="insight-rankings",
                                children=[
                                    html.Div(
                                        className="ranking-item",
                                        children=[
                                            html.Span(f"{i + 1}.", className="ranking-pos"),
                                            html.Span(label, className="ranking-label"),
                                            html.Span(f"{value:,.0f}", className="ranking-value"),
                                            html.Div(
                                                className="ranking-bar",
                                                children=[
                                                    html.Div(
                                                        className="ranking-bar-fill",
                                                        style={
                                                            "width": f"{min(value / series_stats[0][1] * 100, 100):.0f}%",
                                                            "backgroundColor": ["#4F46E5", "#10B981", "#F59E0B",
                                                                               "#EF4444", "#8B5CF6", "#06B6D4",
                                                                               "#F97316", "#EC4899", "#14B8A6"]
                                                            [i % 9],
                                                        },
                                                    )
                                                ],
                                            ),
                                        ],
                                    )
                                    for i, (label, value) in enumerate(series_stats)
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="card",
                children=[
                    html.H2("Key Takeaways", className="card-title"),
                    html.Ul(
                        className="insight-takeaways",
                        children=[
                            html.Li(
                                f"Promotions increase demand by an average of {insights['promotion_uplift_pct']:.1f}% across all series. "
                                f"Strategically placing promotions during trough months (e.g., {list(insights['trough_months'].values())[0] if insights['trough_months'] else 'low-demand periods'}) "
                                f"could help smooth demand fluctuations."
                            ),
                            html.Li(
                                f"The highest-demand product is '{insights['highest_demand_sku']}' "
                                f"and the highest-performing supermarket is '{insights['highest_demand_market']}'. "
                                f"Consider allocating additional promotional inventory to these."
                            ),
                            html.Li(
                                "LightGBM achieves the lowest WAPE (9.3%) among all models, making it the recommended "
                                "choice for production forecasting. Prophet provides valuable confidence intervals "
                                "for risk assessment."
                            ),
                            html.Li(
                                "The 8-week direct multi-step forecasting horizon enables production planning "
                                "for the next two months. Re-run forecasts weekly as new sales data arrives."
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def _insight_card(title, value, subtitle, color):
    return html.Div(
        className="insight-card",
        style={"borderTop": f"4px solid {color}"},
        children=[
            html.Span(title, className="insight-card-title"),
            html.Span(str(value), className="insight-card-value"),
            html.Span(subtitle, className="insight-card-subtitle"),
        ],
    )
