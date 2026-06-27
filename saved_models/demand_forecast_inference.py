"""
demand_forecast_inference.py
Standalone inference module. Only needs:
    pip install onnxruntime prophet pandas numpy

No lightgbm package required at runtime for the ONNX path.

FastAPI example
---------------
from demand_forecast_inference import forecast_lgbm, forecast_prophet

@app.get("/forecast/lgbm")
def lgbm_endpoint(sku: str, supermarket: str, ref_week: str):
    preds = forecast_lgbm(sku, supermarket, ref_week, is_promo=[0]*8)
    return {"weeks": preds}

@app.get("/forecast/prophet")
def prophet_endpoint(sku: str, supermarket: str, ref_week: str):
    df = forecast_prophet(sku, supermarket, ref_week, is_promo=[0]*8)
    return df.to_dict(orient="records")
"""

import json
import pickle
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from onnxruntime import InferenceSession


MODEL_DIR = Path(__file__).parent
HORIZON = 8

SKUS = ["Free Range Eggs", "Organic Milk", "Whole Wheat Bread"]
MARKETS = ["DailyNeeds", "FreshMart", "GreenBasket"]

T0 = pd.Timestamp("2019-01-07")


with open(MODEL_DIR / "lgbm_meta.json") as f:
    _META = json.load(f)

FEATURE_COLS = _META["feature_cols"]
LGBM_SESSIONS = {
    h: InferenceSession(str(MODEL_DIR / f"lgbm_h{h}.onnx"))
    for h in range(1, HORIZON + 1)
}


def _build_row(sku, supermarket, ref_week, h, is_promo_h, history):
    """
    Build a single float32 feature vector for horizon h.

    Parameters
    ----------
    ref_week   : str | Timestamp   last observed Monday
    h          : int               horizon step (1-8)
    is_promo_h : int               1 if the target week has a promotion
    history    : pd.Series         index=Timestamp (weekly), values=demand
                                   Pass an empty Series if unavailable -
                                   lag/rolling features will default to 0.
    """
    ref = pd.Timestamp(ref_week)
    target_week = ref + pd.Timedelta(weeks=h)

    row = {
        "is_promo": int(is_promo_h),
        "week_of_year": int(target_week.isocalendar()[1]),
        "month": target_week.month,
        "quarter": (target_week.month - 1) // 3 + 1,
        "year": target_week.year,
        "t_idx": int((target_week - T0) / pd.Timedelta(weeks=1)),
    }

    history_sorted = history.sort_index()
    for lag in [4, 8, 13, 26, 52]:
        lag_date = ref - pd.Timedelta(weeks=lag - 1)
        idx = history_sorted.index.asof(lag_date) if len(history_sorted) else None
        row[f"lag_{lag}"] = float(history_sorted[idx]) if idx is not None else 0.0

    recent = history_sorted[history_sorted.index <= ref]
    for w in [4, 8, 13]:
        window = recent.tail(w)
        row[f"roll_mean_{w}"] = float(window.mean()) if len(window) > 0 else 0.0
        row[f"roll_std_{w}"] = float(window.std()) if len(window) > 1 else 0.0

    for s in SKUS:
        row[f"sku_{s}"] = int(s == sku)
    for m in MARKETS:
        row[f"supermarket_{m}"] = int(m == supermarket)

    vec = np.array([row.get(c, 0.0) for c in FEATURE_COLS], dtype=np.float32)
    return np.nan_to_num(vec, nan=0.0).reshape(1, -1)


def forecast_lgbm(
    sku: str,
    supermarket: str,
    ref_week: str,
    is_promo: list,
    history: pd.Series = None,
) -> list:
    """
    8-week demand forecast via LightGBM ONNX (no Python ML deps at runtime).

    Parameters
    ----------
    sku, supermarket : str
    ref_week         : str   ISO date of the last known week, e.g. "2021-09-06"
    is_promo         : list  length-8 binary flags (1 = promotion that week)
    history          : pd.Series  optional - index=Timestamp, values=weekly demand
                       Providing history enables accurate lag/rolling features.

    Returns
    -------
    list of 8 floats - weekly demand forecasts
    """
    if history is None:
        history = pd.Series(dtype=float)

    preds = []
    for h in range(1, HORIZON + 1):
        sess = LGBM_SESSIONS[h]
        X = _build_row(sku, supermarket, ref_week, h, is_promo[h - 1], history)
        p = sess.run(None, {sess.get_inputs()[0].name: X})[0][0]
        preds.append(round(max(0.0, float(p)), 2))

    return preds


def forecast_prophet(
    sku: str,
    supermarket: str,
    ref_week: str,
    is_promo: list,
) -> pd.DataFrame:
    """
    8-week demand forecast via Prophet with confidence intervals.

    Returns
    -------
    pd.DataFrame - columns: [ds, yhat, yhat_lower, yhat_upper]
    """
    key = f"{sku}__{supermarket}".replace(" ", "_")
    pkl_path = MODEL_DIR / "prophet" / f"prophet_{key}.pkl"

    with open(pkl_path, "rb") as f:
        model = pickle.load(f)

    future_weeks = [
        pd.Timestamp(ref_week) + pd.Timedelta(weeks=h)
        for h in range(1, HORIZON + 1)
    ]
    future = pd.DataFrame({
        "ds": future_weeks,
        "is_promo": [int(p) for p in is_promo],
    })

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fc = model.predict(future)

    fc["yhat"] = fc["yhat"].clip(lower=0)
    return fc[["ds", "yhat", "yhat_lower", "yhat_upper"]].reset_index(drop=True)


if __name__ == "__main__":
    SKU = "Organic Milk"
    MARKET = "DailyNeeds"
    WEEK = "2021-09-06"
    PROMO = [0, 0, 0, 1, 0, 0, 0, 0]

    print("LightGBM (ONNX)")
    for h, p in enumerate(forecast_lgbm(SKU, MARKET, WEEK, PROMO), 1):
        print(f"  Week +{h}: {p:.1f} units")

    print("\nProphet")
    print(forecast_prophet(SKU, MARKET, WEEK, PROMO).to_string(index=False))
