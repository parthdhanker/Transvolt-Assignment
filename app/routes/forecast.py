import logging
import pandas as pd
from flask import Blueprint, request, jsonify
from app.services.forecast_service import generate_forecast
from app.services.data_service import get_history

logger = logging.getLogger("demand-forecast.api")

forecast_bp = Blueprint("forecast", __name__)

ALLOWED_SKUS = ["Free Range Eggs", "Organic Milk", "Whole Wheat Bread"]
ALLOWED_MARKETS = ["DailyNeeds", "FreshMart", "GreenBasket"]
ALLOWED_MODELS = ["lgbm", "prophet"]


def validate_params(args: dict) -> tuple:
    sku = args.get("sku")
    market = args.get("market")
    ref_week = args.get("ref_week")
    model = args.get("model", "lgbm")
    is_promo_raw = args.get("is_promo")

    errors = []
    if sku not in ALLOWED_SKUS:
        errors.append(f"sku must be one of {ALLOWED_SKUS}")
    if market not in ALLOWED_MARKETS:
        errors.append(f"market must be one of {ALLOWED_MARKETS}")
    if model not in ALLOWED_MODELS:
        errors.append(f"model must be one of {ALLOWED_MODELS}")
    if not ref_week:
        errors.append("ref_week is required (YYYY-MM-DD)")

    if is_promo_raw:
        parts = is_promo_raw.split(",")
        if len(parts) != 8:
            errors.append("is_promo must be 8 comma-separated 0/1 values")
        else:
            try:
                is_promo = [int(p) for p in parts]
                if any(p not in (0, 1) for p in is_promo):
                    errors.append("is_promo values must be 0 or 1")
            except ValueError:
                errors.append("is_promo must be comma-separated integers")
    else:
        is_promo = [0] * 8

    return errors, sku, market, ref_week, model, is_promo


@forecast_bp.route("/api/forecast", methods=["GET"])
def forecast():
    errors, sku, market, ref_week, model, is_promo = validate_params(request.args)

    if errors:
        return jsonify({"error": "; ".join(errors), "status": 400}), 400

    try:
        history = get_history(sku, market)
        history_before = history[history.index <= pd.Timestamp(ref_week)]

        result = generate_forecast(sku, market, ref_week, model, is_promo, history_before)
        return jsonify({"status": "ok", "data": result})
    except Exception as e:
        logger.exception("Forecast failed")
        return jsonify({"error": str(e), "status": 500}), 500
