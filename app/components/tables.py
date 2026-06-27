from dash import dash_table, html


def create_data_table(df, id="table", page_size=10):
    columns = [
        {"name": c.replace("_", " ").title(), "id": c}
        for c in df.columns
    ]
    return dash_table.DataTable(
        id=id,
        columns=columns,
        data=df.to_dict("records"),
        page_size=page_size,
        style_table={"overflowX": "auto", "borderRadius": "8px"},
        style_header={
            "backgroundColor": "#F8FAFC",
            "color": "#475569",
            "fontWeight": "600",
            "fontSize": "13px",
            "borderBottom": "2px solid #E2E8F0",
            "padding": "12px 16px",
            "fontFamily": "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
        },
        style_cell={
            "padding": "10px 16px",
            "fontSize": "13px",
            "color": "#1E293B",
            "borderBottom": "1px solid #F1F5F9",
            "fontFamily": "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
        },
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#F8FAFC",
            }
        ],
    )


def forecast_table(forecast_result):
    rows = forecast_result["weeks"]
    preds = forecast_result["predictions"]
    promo_weeks = set(forecast_result.get("promo_weeks", []))
    ci = forecast_result.get("ci")

    data = []
    for i, (week, pred) in enumerate(zip(rows, preds)):
        row = {
            "week": week,
            "forecast": pred,
            "promo": "Yes" if (i + 1) in promo_weeks else "No",
        }
        if ci:
            row["ci_lower"] = ci["lower"][i]
            row["ci_upper"] = ci["upper"][i]
        data.append(row)

    columns_def = [
        {"name": "Week", "id": "week"},
        {"name": "Forecast", "id": "forecast", "type": "numeric", "format": {"specifier": ".0f"}},
        {"name": "Promotion", "id": "promo"},
    ]
    if ci:
        columns_def.append({"name": "CI Lower", "id": "ci_lower", "type": "numeric", "format": {"specifier": ".0f"}})
        columns_def.append({"name": "CI Upper", "id": "ci_upper", "type": "numeric", "format": {"specifier": ".0f"}})

    return dash_table.DataTable(
        columns=columns_def,
        data=data,
        page_size=8,
        style_table={"overflowX": "auto", "borderRadius": "8px"},
        style_header={
            "backgroundColor": "#F8FAFC",
            "color": "#475569",
            "fontWeight": "600",
            "fontSize": "13px",
            "borderBottom": "2px solid #E2E8F0",
            "padding": "10px 14px",
            "fontFamily": "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
        },
        style_cell={
            "padding": "8px 14px",
            "fontSize": "13px",
            "color": "#1E293B",
            "borderBottom": "1px solid #F1F5F9",
            "fontFamily": "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
        },
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#F8FAFC",
            },
            {
                "if": {"column_id": "promo", "filter_query": '{promo} = "Yes"'},
                "color": "#10B981",
                "fontWeight": "600",
            },
        ],
    )
