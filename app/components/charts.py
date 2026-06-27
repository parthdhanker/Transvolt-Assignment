import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

CHART_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToAdd": ["drawline", "drawopenpath", "eraseshape"],
    "modeBarButtonsToRemove": ["sendDataToCloud", "lasso2d", "select2d"],
    "responsive": True,
    "scrollZoom": True,
    "toImageButtonOptions": {
        "format": "png",
        "filename": "demand-forecast-chart",
        "height": 600,
        "width": 1200,
    },
}

THEME = {
    "indigo": "#4F46E5",
    "indigo_light": "#EEF2FF",
    "indigo_dark": "#3730A3",
    "green": "#10B981",
    "red": "#EF4444",
    "amber": "#F59E0B",
    "slate_300": "#CBD5E1",
    "slate_400": "#94A3B8",
    "slate_500": "#64748B",
    "slate_600": "#475569",
    "slate_700": "#334155",
    "white": "#FFFFFF",
}


def _base_layout(title=None, xaxis_title=None, yaxis_title=None):
    return {
        "font": {"family": "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", "size": 12},
        "margin": {"l": 60, "r": 30, "t": 40, "b": 60},
        "legend": {"orientation": "h", "y": -0.25, "x": 0},
        "hovermode": "x unified",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "xaxis": {
            "gridcolor": "#F1F5F9",
            "zerolinecolor": "#E2E8F0",
            "title": xaxis_title,
        },
        "yaxis": {
            "gridcolor": "#F1F5F9",
            "zerolinecolor": "#E2E8F0",
            "title": yaxis_title,
        },
        "title": {"text": title, "x": 0.5, "xanchor": "center"},
    }


def forecast_chart(history_df, forecast_result, model_name):
    fig = go.Figure()

    if history_df is not None and len(history_df) > 0:
        promo_mask = history_df["is_promo"] == 1 if "is_promo" in history_df.columns else None
        fig.add_trace(go.Scatter(
            x=history_df["week"],
            y=history_df["demand"],
            mode="lines",
            name="Historical Demand",
            line=dict(color=THEME["slate_400"], width=2),
            hovertemplate="%{x|%b %d, %Y}<br>Demand: %{y:.0f}<extra>Historical</extra>",
        ))

        if promo_mask is not None and promo_mask.any():
            promo_df = history_df[promo_mask]
            fig.add_trace(go.Scatter(
                x=promo_df["week"],
                y=promo_df["demand"],
                mode="markers",
                name="Past Promotions",
                marker=dict(color=THEME["amber"], size=8, symbol="star"),
                hovertemplate="%{x|%b %d, %Y}<br>Demand: %{y:.0f}<br>Promotion Week<extra></extra>",
            ))

    forecast_weeks = pd.to_datetime(forecast_result["weeks"])
    preds = forecast_result["predictions"]

    color = THEME["indigo"] if model_name == "lgbm" else THEME["green"]
    name = "LightGBM Forecast" if model_name == "lgbm" else "Prophet Forecast"

    if forecast_result.get("ci"):
        fig.add_trace(go.Scatter(
            x=forecast_weeks,
            y=forecast_result["ci"]["upper"],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=forecast_weeks,
            y=forecast_result["ci"]["lower"],
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(16, 185, 129, 0.15)",
            name="Confidence Interval",
            hovertemplate="%{x|%b %d, %Y}<br>Lower: %{y:.0f}<extra>CI</extra>",
        ))

    fig.add_trace(go.Scatter(
        x=forecast_weeks,
        y=preds,
        mode="lines+markers",
        name=name,
        line=dict(color=color, width=3),
        marker=dict(size=8, color=color),
        hovertemplate="%{x|%b %d, %Y}<br>Forecast: %{y:.0f}<extra></extra>",
    ))

    promo_week_indices = forecast_result.get("promo_weeks", [])
    for pw in promo_week_indices:
        if pw <= len(forecast_weeks):
            fig.add_vline(
                x=pd.Timestamp(forecast_weeks[pw - 1]),
                line_dash="dash",
                line_color=THEME["amber"],
                line_width=1.5,
                opacity=0.6,
            )

    fig.add_vline(
        x=pd.Timestamp(forecast_result["ref_week"]),
        line_dash="dot",
        line_color=THEME["red"],
        line_width=1.5,
        opacity=0.5,
    )

    fig.add_annotation(
        x=pd.Timestamp(forecast_result["ref_week"]),
        y=1,
        yref="paper",
        text="Forecast Start",
        showarrow=False,
        font=dict(size=10, color=THEME["red"]),
        yshift=10,
    )

    fig.update_layout(**_base_layout(
        title=None,
        yaxis_title="Weekly Demand (units)",
    ))
    fig.update_layout(legend=dict(orientation="h", y=-0.3, x=0))

    return fig


def time_series_chart(df, x_col, y_col, color_col=None, title=None):
    fig = px.line(
        df, x=x_col, y=y_col, color=color_col,
        color_discrete_sequence=[THEME["indigo"], THEME["green"], THEME["amber"], THEME["red"]],
    )
    fig.update_traces(line=dict(width=2))
    fig.update_layout(**_base_layout(title=title, yaxis_title="Demand"))
    fig.update_layout(legend=dict(orientation="h", y=-0.3, x=0))
    fig.update_xaxes(rangeslider_visible=True)
    return fig


def bar_chart(df, x_col, y_col, color_col=None, title=None, barmode="group"):
    fig = px.bar(
        df, x=x_col, y=y_col, color=color_col, barmode=barmode,
        color_discrete_sequence=[THEME["indigo"], THEME["green"], THEME["amber"], THEME["red"]],
    )
    fig.update_layout(**_base_layout(title=title, yaxis_title="Demand"))
    fig.update_layout(legend=dict(orientation="h", y=-0.3, x=0))
    return fig


def box_chart(df, x_col, y_col, color_col=None, title=None):
    fig = px.box(
        df, x=x_col, y=y_col, color=color_col,
        color_discrete_sequence=[THEME["indigo"], THEME["green"], THEME["amber"]],
        points="outliers",
    )
    fig.update_layout(**_base_layout(title=title, yaxis_title="Demand"))
    fig.update_layout(legend=dict(orientation="h", y=-0.3, x=0))
    return fig


def heatmap_chart(df, x_col, y_col, z_col, title=None):
    pivot = df.pivot_table(index=y_col, columns=x_col, values=z_col, aggfunc="mean")
    fig = px.imshow(
        pivot.values,
        x=list(pivot.columns),
        y=list(pivot.index),
        color_continuous_scale="Blues",
        aspect="auto",
        labels={"x": x_col, "y": y_col, "color": "Demand"},
    )
    fig.update_layout(**_base_layout(title=title))
    fig.update_xaxes(tickangle=45)
    return fig


def model_comparison_chart(history_df, lgbm_result, prophet_result):
    fig = go.Figure()

    if history_df is not None and len(history_df) > 0:
        fig.add_trace(go.Scatter(
            x=history_df["week"],
            y=history_df["demand"],
            mode="lines",
            name="Historical",
            line=dict(color=THEME["slate_400"], width=1.5),
        ))

    forecast_weeks = pd.to_datetime(lgbm_result["weeks"])

    fig.add_trace(go.Scatter(
        x=forecast_weeks,
        y=lgbm_result["predictions"],
        mode="lines+markers",
        name="LightGBM",
        line=dict(color=THEME["indigo"], width=3),
        marker=dict(size=7),
    ))

    if prophet_result.get("ci"):
        fig.add_trace(go.Scatter(
            x=forecast_weeks,
            y=prophet_result["ci"]["upper"],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=forecast_weeks,
            y=prophet_result["ci"]["lower"],
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(16, 185, 129, 0.1)",
            name="Prophet CI",
        ))

    fig.add_trace(go.Scatter(
        x=forecast_weeks,
        y=prophet_result["predictions"],
        mode="lines+markers",
        name="Prophet",
        line=dict(color=THEME["green"], width=3, dash="dash"),
        marker=dict(size=7),
    ))

    fig.update_layout(**_base_layout(
        title=None,
        yaxis_title="Weekly Demand (units)",
    ))
    fig.update_layout(legend=dict(orientation="h", y=-0.3, x=0))
    return fig


def promo_comparison_chart(comparison_df):
    fig = go.Figure()
    for status in ["No Promo", "Promo"]:
        subset = comparison_df[comparison_df["status"] == status]
        fig.add_trace(go.Bar(
            name=status,
            x=subset["label"],
            y=subset["demand"],
            marker_color=THEME["slate_400"] if status == "No Promo" else THEME["indigo"],
            hovertemplate="%{x}<br>%{y:.0f}<extra></extra>",
        ))
    fig.update_layout(
        barmode="group",
        **_base_layout(title=None, yaxis_title="Mean Weekly Demand"),
    )
    fig.update_layout(legend=dict(orientation="h", y=-0.3, x=0))
    return fig
