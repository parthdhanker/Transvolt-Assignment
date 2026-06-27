import logging
import pandas as pd
import numpy as np
from app.services.data_service import get_weekly, get_stats

logger = logging.getLogger("demand-forecast.insights")

_cache = None


def compute_insights() -> dict:
    global _cache
    if _cache is not None:
        return _cache

    weekly = get_weekly()

    total_by_sku = weekly.groupby("sku")["demand"].sum()
    total_by_market = weekly.groupby("supermarket")["demand"].sum()

    mean_by_sku_market = weekly.groupby(["sku", "supermarket"])["demand"].mean()

    promo = weekly[weekly["is_promo"] == 1]
    no_promo = weekly[weekly["is_promo"] == 0]

    overall_promo_mean = promo["demand"].mean() if len(promo) > 0 else 0
    overall_no_promo_mean = no_promo["demand"].mean() if len(no_promo) > 0 else 1
    promo_uplift = ((overall_promo_mean - overall_no_promo_mean) / overall_no_promo_mean * 100)

    monthly = weekly.copy()
    monthly["month"] = monthly["week"].dt.month
    monthly_avg = monthly.groupby(["sku", "month"])["demand"].mean().reset_index()
    peak_months = {}
    trough_months = {}
    for sku in monthly_avg["sku"].unique():
        s = monthly_avg[monthly_avg["sku"] == sku]
        peak_months[sku] = int(s.loc[s["demand"].idxmax(), "month"])
        trough_months[sku] = int(s.loc[s["demand"].idxmin(), "month"])

    yearly = weekly.copy()
    yearly["year"] = yearly["week"].dt.year
    yearly_avg = yearly.groupby(["sku", "year"])["demand"].mean().reset_index()
    trend_direction = {}
    for sku in yearly_avg["sku"].unique():
        s = yearly_avg[yearly_avg["sku"] == sku].sort_values("year")
        if len(s) >= 2:
            first = s.iloc[0]["demand"]
            last = s.iloc[-1]["demand"]
            trend_direction[sku] = "up" if last > first else "down"
        else:
            trend_direction[sku] = "stable"

    stats = get_stats()
    _cache = {
        "highest_demand_sku": total_by_sku.idxmax(),
        "highest_demand_sku_value": round(float(total_by_sku.max()), 2),
        "highest_demand_market": total_by_market.idxmax(),
        "highest_demand_market_value": round(float(total_by_market.max()), 2),
        "average_weekly_demand": round(float(weekly["demand"].mean()), 2),
        "median_weekly_demand": round(float(weekly["demand"].median()), 2),
        "total_demand": round(float(weekly["demand"].sum()), 2),
        "promotion_uplift_pct": round(float(promo_uplift), 1),
        "promo_weeks_count": int(promo["week"].nunique()),
        "total_weeks": int(weekly["week"].nunique()),
        "peak_months": peak_months,
        "trough_months": trough_months,
        "trend_direction": trend_direction,
        "num_series": stats["num_series"],
        "date_range": f"{stats['date_min']} to {stats['date_max']}",
        "sku_list": stats["sku_list"],
        "market_list": stats["market_list"],
        "mean_by_sku_market": {
            f"{s} @ {m}": round(float(v), 2)
            for (s, m), v in mean_by_sku_market.items()
        },
    }
    logger.info("Business insights computed")
    return _cache
