import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash.exceptions
import pandas as pd
from app.services.data_service import get_weekly, get_series, get_ref_weeks, get_history
from app.services.forecast_service import generate_forecast, get_model_info
from app.components.charts import forecast_chart, CHART_CONFIG
from app.components.tables import forecast_table

dash.register_page(__name__, path="/forecast")


def layout():
    series = get_series()
    ref_weeks = get_ref_weeks()
    model_info = get_model_info()

    return html.Div(
        className="page-content",
        children=[
            html.Div(
                className="page-header",
                children=[
                    html.H1("Forecast Explorer", className="page-title"),
                    html.P("Generate 8-week demand forecasts with promotion simulation", className="page-desc"),
                ],
            ),
            html.Div(
                className="forecast-controls card",
                children=[
                    html.Div(
                        className="filter-row",
                        children=[
                            html.Div(
                                className="filter-group",
                                children=[
                                    html.Label("Supermarket", className="filter-label"),
                                    dcc.Dropdown(
                                        id="forecast-market",
                                        options=[{"label": m, "value": m} for m in sorted(set(m for _, m in series))],
                                        value="DailyNeeds",
                                        clearable=False,
                                        className="filter-dropdown",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="filter-group",
                                children=[
                                    html.Label("SKU", className="filter-label"),
                                    dcc.Dropdown(
                                        id="forecast-sku",
                                        options=[{"label": s, "value": s} for s in sorted(set(s for s, _ in series))],
                                        value="Organic Milk",
                                        clearable=False,
                                        className="filter-dropdown",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="filter-group",
                                children=[
                                    html.Label("Reference Week", className="filter-label"),
                                    dcc.Dropdown(
                                        id="forecast-ref-week",
                                        options=[{"label": w, "value": w} for w in ref_weeks],
                                        value=ref_weeks[-1] if ref_weeks else None,
                                        clearable=False,
                                        className="filter-dropdown",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="filter-group",
                                children=[
                                    html.Label("Model", className="filter-label"),
                                    dcc.Dropdown(
                                        id="forecast-model",
                                        options=[
                                            {"label": f"LightGBM (WAPE {model_info.get('wape', 'N/A')})", "value": "lgbm"},
                                            {"label": "Prophet (with CI)", "value": "prophet"},
                                        ],
                                        value="lgbm",
                                        clearable=False,
                                        className="filter-dropdown",
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        className="promo-sim-section",
                        children=[
                            html.Label("Promotion Simulation (select future promo weeks)", className="filter-label"),
                            html.Div(
                                className="promo-toggles",
                                id="promo-toggles",
                                children=[
                                    html.Label(
                                        className="promo-toggle",
                                        children=[
                                            dcc.Checklist(
                                                id={"type": "promo-toggle", "index": i},
                                                options=[{"label": f"Week +{i}", "value": i}],
                                                value=[],
                                                className="promo-checkbox",
                                                labelStyle={"display": "flex", "alignItems": "center", "gap": "6px"},
                                            ),
                                        ],
                                    )
                                    for i in range(1, 9)
                                ],
                            ),
                        ],
                    ),
                    html.Button(
                        "Generate Forecast",
                        id="generate-btn",
                        className="btn btn-primary",
                        n_clicks=0,
                    ),
                ],
            ),
            html.Div(id="forecast-output", children=[
                html.Div(
                    className="card-grid-2",
                    children=[
                        html.Div(
                            className="card",
                            children=[
                                html.H2("Forecast Results", className="card-title"),
                                dcc.Loading(
                                    id="loading-forecast",
                                    type="circle",
                                    children=dcc.Graph(
                                        id="forecast-chart",
                                        config=CHART_CONFIG,
                                        figure={},
                                    ),
                                ),
                            ],
                        ),
                        html.Div(
                            className="prediction-details-card",
                            id="prediction-details",
                            children=_empty_details(),
                        ),
                    ],
                ),
                html.Div(
                    className="card",
                    style={"marginTop": "16px"},
                    children=[
                        html.H2("Forecast Table", className="card-title"),
                        html.Div(id="forecast-table-container"),
                    ],
                ),
            ]),
        ],
    )


def _empty_details():
    return html.Div(
        className="prediction-details",
        children=[
            html.H3("Prediction Details", className="details-title"),
            html.P("Generate a forecast to see details here.", className="details-placeholder"),
        ],
    )


def _build_details(forecast_result, model_name):
    meta = get_model_info()
    model_meta = meta.get("lgbm" if model_name == "lgbm" else "prophet", {})

    details = [
        ("Selected Model", f"{model_meta.get('name', model_name)}"),
        ("Model Type", model_meta.get("type", "")),
        ("Model Description", model_meta.get("description", "")),
        ("Reference Week", forecast_result["ref_week"]),
        ("Forecast Horizon", f'{forecast_result["horizon"]} weeks'),
        ("Total Predicted", f'{forecast_result["total"]:,.0f} units'),
        ("Promotion Weeks", ", ".join(f"Week +{w}" for w in forecast_result["promo_weeks"]) if forecast_result["promo_weeks"] else "None"),
    ]

    items = []
    for label, value in details:
        items.append(html.Div(
            className="detail-item",
            children=[
                html.Span(label, className="detail-label"),
                html.Span(str(value), className="detail-value"),
            ],
        ))

    return html.Div(
        className="prediction-details",
        children=[
            html.H3("Prediction Details", className="details-title"),
            html.Div(
                className="details-list",
                children=items,
            ),
        ],
    )


def _get_promo_state(all_checks):
    is_promo = []
    for i in range(1, 9):
        val = all_checks.get(i, [])
        is_promo.append(1 if (isinstance(val, list) and i in val) or val == i else 0)
    return is_promo


@callback(
    Output("forecast-chart", "figure"),
    Output("prediction-details", "children"),
    Output("forecast-table-container", "children"),
    Input("generate-btn", "n_clicks"),
    State("forecast-sku", "value"),
    State("forecast-market", "value"),
    State("forecast-ref-week", "value"),
    State("forecast-model", "value"),
    State({"type": "promo-toggle", "index": dash.dependencies.ALL}, "value"),
    State({"type": "promo-toggle", "index": dash.dependencies.ALL}, "id"),
    prevent_initial_call=True,
)
def on_generate_forecast(n_clicks, sku, market, ref_week, model, check_values, check_ids):
    if not all([sku, market, ref_week]):
        return no_update, no_update, no_update

    is_promo = [0] * 8
    for cid, cval in zip(check_ids, check_values):
        idx = cid["index"] - 1
        if cval and idx >= 0:
            is_promo[idx] = 1

    history = get_history(sku, market)
    history_before = history[history.index <= pd.Timestamp(ref_week)]
    history_df = get_weekly()
    hist_subset = history_df[
        (history_df["sku"] == sku) & (history_df["supermarket"] == market)
    ][["week", "demand", "is_promo"]].sort_values("week")
    hist_subset = hist_subset[hist_subset["week"] <= pd.Timestamp(ref_week)]

    result = generate_forecast(sku, market, ref_week, model, is_promo, history_before)

    fig = forecast_chart(hist_subset.tail(24), result, model)
    fig.update_layout(height=400)

    details = _build_details(result, model)

    table = forecast_table(result)

    return fig, details, table
