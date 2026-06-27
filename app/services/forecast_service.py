import logging
import importlib.util
import sys
from pathlib import Path
import pandas as pd
from app.utils.config import MODELS_DIR, HORIZON

logger = logging.getLogger("demand-forecast.forecast")

_forecaster = None


def _load_module():
    global _forecaster
    if _forecaster is not None:
        return _forecaster

    module_path = MODELS_DIR / "demand_forecast_inference.py"
    spec = importlib.util.spec_from_file_location("demand_forecast_inference", module_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["demand_forecast_inference"] = mod
    spec.loader.exec_module(mod)
    _forecaster = mod
    logger.info("Inference module loaded from %s", module_path)
    return _forecaster


def forecast_lgbm(
    sku: str,
    market: str,
    ref_week: str,
    is_promo: list,
    history: pd.Series,
) -> list:
    mod = _load_module()
    logger.info("LGBM forecast: %s @ %s ref=%s promo=%s", sku, market, ref_week, is_promo)
    preds = mod.forecast_lgbm(sku, market, ref_week, is_promo, history)
    return preds


def forecast_prophet(
    sku: str,
    market: str,
    ref_week: str,
    is_promo: list,
) -> pd.DataFrame:
    mod = _load_module()
    logger.info("Prophet forecast: %s @ %s ref=%s promo=%s", sku, market, ref_week, is_promo)
    df = mod.forecast_prophet(sku, market, ref_week, is_promo)
    return df


def get_model_info() -> dict:
    return {
        "lgbm": {
            "name": "LightGBM (ONNX)",
            "type": "Direct Multi-step (8 horizon models)",
            "description": "Fast, accurate gradient boosting with engineered features (lags, rolling statistics, calendar, entity dummies). Uses ONNX runtime - no LightGBM Python package needed.",
            "version": "1.0",
        },
        "prophet": {
            "name": "Prophet",
            "type": "Additive trend + yearly seasonality + promotion regressor",
            "description": "Facebook Prophet with yearly seasonality, changepoint detection, and promotion regressor. Provides confidence intervals via Stan backend.",
            "version": "1.1.6",
        },
        "horizon": HORIZON,
    }


def generate_forecast(
    sku: str,
    market: str,
    ref_week: str,
    model: str,
    is_promo: list,
    history: pd.Series,
):
    weeks = [
        (pd.Timestamp(ref_week) + pd.Timedelta(weeks=h)).strftime("%Y-%m-%d")
        for h in range(1, HORIZON + 1)
    ]

    if model == "lgbm":
        preds = forecast_lgbm(sku, market, ref_week, is_promo, history)
        return {
            "model": "LightGBM (ONNX)",
            "ref_week": ref_week,
            "horizon": HORIZON,
            "promo_weeks": [i + 1 for i, p in enumerate(is_promo) if p == 1],
            "weeks": weeks,
            "predictions": preds,
            "total": round(sum(preds), 2),
            "ci": None,
        }
    else:
        df = forecast_prophet(sku, market, ref_week, is_promo)
        preds = [round(max(0.0, v), 2) for v in df["yhat"].tolist()]
        ci_lower = [round(max(0.0, v), 2) for v in df["yhat_lower"].tolist()]
        ci_upper = [round(max(0.0, v), 2) for v in df["yhat_upper"].tolist()]
        return {
            "model": "Prophet",
            "ref_week": ref_week,
            "horizon": HORIZON,
            "promo_weeks": [i + 1 for i, p in enumerate(is_promo) if p == 1],
            "weeks": weeks,
            "predictions": preds,
            "total": round(sum(preds), 2),
            "ci": {
                "lower": ci_lower,
                "upper": ci_upper,
            },
        }
