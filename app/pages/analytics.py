import dash
from dash import html, dcc, callback, Input, Output
import plotly.express as px
import pandas as pd
from app.services.data_service import get_weekly, get_series
from app.services.forecast_service import get_model_info, generate_forecast
from app.services.data_service import get_history
from app.components.charts import (
    CHART_CONFIG, THEME, time_series_chart,
    model_comparison_chart,
)

dash.register_page(__name__, path="/analytics")


def layout():
    return html.Div(
        className="page-content",
        children=[
            html.Div(
                className="page-header",
                children=[
                    html.H1("Analytics", className="page-title"),
                    html.P("Historical trends and model comparison", className="page-desc"),
                ],
            ),
            dcc.Tabs(
                id="analytics-tabs",
                value="historical",
                className="analytics-tabs",
                children=[
                    dcc.Tab(label="Historical Analysis", value="historical", className="analytics-tab", selected_className="analytics-tab-selected"),
                    dcc.Tab(label="Model Comparison", value="models", className="analytics-tab", selected_className="analytics-tab-selected"),
                ],
            ),
            html.Div(id="analytics-content", className="analytics-content"),
        ],
    )


@callback(Output("analytics-content", "children"), Input("analytics-tabs", "value"))
def render_tab(tab):
    if tab == "historical":
        return _historical_tab()
    return _models_tab()


def _historical_tab():
    weekly = get_weekly()

    monthly = weekly.copy()
    monthly["month"] = monthly["week"].dt.month
    monthly["year"] = monthly["week"].dt.year
    monthly_agg = monthly.groupby(["year", "month"])["demand"].sum().reset_index()
    monthly_agg["period"] = monthly_agg.apply(lambda r: f"{int(r['year'])}-{int(r['month']):02d}", axis=1)

    monthly_sku = monthly.groupby(["month", "sku"])["demand"].mean().reset_index()
    fig_seasonality = px.line(
        monthly_sku, x="month", y="demand", color="sku",
        color_discrete_sequence=[THEME["indigo"], THEME["green"], THEME["amber"]],
        markers=True,
    )
    fig_seasonality.update_traces(line=dict(width=2))
    fig_seasonality.update_layout(
        title="Monthly Seasonality by SKU",
        xaxis=dict(tickmode="array", tickvals=list(range(1, 13)),
                    ticktext=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]),
        yaxis_title="Mean Weekly Demand",
        font={"family": "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", "size": 12},
        margin={"l": 50, "r": 20, "t": 40, "b": 50},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend={"orientation": "h", "y": -0.3, "x": 0},
    )

    yearly = weekly.copy()
    yearly["year"] = yearly["week"].dt.year
    yearly_avg = yearly.groupby(["sku", "supermarket", "year"])["demand"].mean().reset_index()
    yearly_avg["series"] = yearly_avg["sku"] + " @ " + yearly_avg["supermarket"]
    fig_yoy = px.line(
        yearly_avg, x="year", y="demand", color="series",
        color_discrete_sequence=px.colors.qualitative.Set2,
        markers=True,
    )
    fig_yoy.update_traces(line=dict(width=2))
    fig_yoy.update_layout(
        title="Year-over-Year Trend by Series",
        yaxis_title="Mean Weekly Demand",
        font={"family": "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", "size": 12},
        margin={"l": 50, "r": 20, "t": 40, "b": 50},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend={"orientation": "h", "y": -0.3, "x": 0},
    )

    return html.Div(
        className="tab-content",
        children=[
            html.Div(
                className="card",
                children=[
                    html.H2("Seasonality", className="card-title"),
                    dcc.Loading(type="circle", children=dcc.Graph(figure=fig_seasonality, config=CHART_CONFIG)),
                ],
            ),
            html.Div(
                className="card",
                children=[
                    html.H2("Year-over-Year Trend", className="card-title"),
                    dcc.Loading(type="circle", children=dcc.Graph(figure=fig_yoy, config=CHART_CONFIG)),
                ],
            ),
        ],
    )


def _models_tab():
    meta = get_model_info()

    weekly = get_weekly()
    s = weekly[(weekly["sku"] == "Organic Milk") & (weekly["supermarket"] == "DailyNeeds")]
    history = s.set_index("week")["demand"].sort_index()
    ref_week = "2021-09-06"
    history_before = history[history.index <= pd.Timestamp(ref_week)]
    hist_df = s[s["week"] <= pd.Timestamp(ref_week)][["week", "demand", "is_promo"]].sort_values("week")

    lgbm_result = generate_forecast("Organic Milk", "DailyNeeds", ref_week, "lgbm", [0, 0, 0, 1, 0, 0, 0, 0], history_before)
    prophet_result = generate_forecast("Organic Milk", "DailyNeeds", ref_week, "prophet", [0, 0, 0, 1, 0, 0, 0, 0], history_before)

    fig_compare = model_comparison_chart(hist_df.tail(20), lgbm_result, prophet_result)
    fig_compare.update_layout(height=400)

    return html.Div(
        className="tab-content",
        children=[
            html.Div(
                className="card-grid-2",
                children=[
                    html.Div(
                        className="card model-card",
                        children=[
                            html.Div(
                                className="model-card-header",
                                children=[
                                    html.Div(className="model-icon", style={"backgroundColor": "#EEF2FF", "color": "#4F46E5"}, children="L"),
                                    html.H2("LightGBM (ONNX)", className="card-title"),
                                ],
                            ),
                            html.Div(
                                className="model-card-body",
                                children=[
                                    html.P(meta["lgbm"]["description"], className="model-desc"),
                                    html.Div(
                                        className="model-stats",
                                        children=[
                                            html.Div(className="model-stat", children=[html.Span("Type", className="ms-label"), html.Span("Gradient Boosting", className="ms-value")]),
                                            html.Div(className="model-stat", children=[html.Span("Architecture", className="ms-label"), html.Span("Direct Multi-step (8 models)", className="ms-value")]),
                                            html.Div(className="model-stat", children=[html.Span("Features", className="ms-label"), html.Span("Calendar, Lags, Rolling, Entity dummies", className="ms-value")]),
                                            html.Div(className="model-stat", children=[html.Span("Runtime", className="ms-label"), html.Span("ONNX Runtime (no LightGBM)", className="ms-value")]),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        className="card model-card",
                        children=[
                            html.Div(
                                className="model-card-header",
                                children=[
                                    html.Div(className="model-icon", style={"backgroundColor": "#ECFDF5", "color": "#10B981"}, children="P"),
                                    html.H2("Prophet", className="card-title"),
                                ],
                            ),
                            html.Div(
                                className="model-card-body",
                                children=[
                                    html.P(meta["prophet"]["description"], className="model-desc"),
                                    html.Div(
                                        className="model-stats",
                                        children=[
                                            html.Div(className="model-stat", children=[html.Span("Type", className="ms-label"), html.Span("Additive Seasonality", className="ms-value")]),
                                            html.Div(className="model-stat", children=[html.Span("Seasonality", className="ms-label"), html.Span("Yearly (weekly=False)", className="ms-value")]),
                                            html.Div(className="model-stat", children=[html.Span("Regressor", className="ms-label"), html.Span("is_promo (extra regressor)", className="ms-value")]),
                                            html.Div(className="model-stat", children=[html.Span("Output", className="ms-label"), html.Span("Point forecast + Confidence Intervals", className="ms-value")]),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="card",
                children=[
                    html.H2("Model Comparison: LightGBM vs Prophet", className="card-title"),
                    html.P("Same scenario: Organic Milk @ DailyNeeds, reference week 2021-09-06", className="card-subtitle"),
                    dcc.Loading(
                        type="circle",
                        children=dcc.Graph(figure=fig_compare, config=CHART_CONFIG),
                    ),
                ],
            ),
        ],
    )
