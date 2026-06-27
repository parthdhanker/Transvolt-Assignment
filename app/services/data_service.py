import logging
import pandas as pd
from app.utils.config import DEMAND_CSV, PROMOTIONS_CSV
from app.utils.data_loader import load_demand, load_promotions, build_weekly, get_series_list, get_reference_weeks

logger = logging.getLogger("demand-forecast.data")

_weekly: pd.DataFrame = None
_series_list: list = None
_ref_weeks: list = None
_demand_raw: pd.DataFrame = None
_promotions_raw: pd.DataFrame = None


def init_data():
    global _weekly, _series_list, _ref_weeks, _demand_raw, _promotions_raw

    logger.info("Loading demand.csv...")
    _demand_raw = load_demand(DEMAND_CSV)
    logger.info("demand.csv loaded: %d rows", len(_demand_raw))

    logger.info("Loading promotions.csv...")
    _promotions_raw = load_promotions(PROMOTIONS_CSV)
    logger.info("promotions.csv loaded: %d rows", len(_promotions_raw))

    logger.info("Building weekly aggregation...")
    _weekly = build_weekly(_demand_raw, _promotions_raw)
    logger.info("Weekly data: %d rows, %d weeks", len(_weekly), _weekly["week"].nunique())

    _series_list = get_series_list(_weekly)
    _ref_weeks = get_reference_weeks(_weekly)

    logger.info("Series: %d | Reference weeks: %d", len(_series_list), len(_ref_weeks))


def get_weekly() -> pd.DataFrame:
    if _weekly is None:
        init_data()
    return _weekly


def get_series() -> list:
    if _series_list is None:
        init_data()
    return _series_list


def get_ref_weeks() -> list:
    if _ref_weeks is None:
        init_data()
    return _ref_weeks


def get_history(sku: str, market: str) -> pd.Series:
    weekly = get_weekly()
    s = weekly[(weekly["sku"] == sku) & (weekly["supermarket"] == market)]
    return s.set_index("week")["demand"].sort_index()


def get_promo_history(sku: str, market: str) -> pd.Series:
    weekly = get_weekly()
    s = weekly[(weekly["sku"] == sku) & (weekly["supermarket"] == market)]
    return s.set_index("week")["is_promo"].sort_index()


def get_stats() -> dict:
    weekly = get_weekly()
    series = get_series()
    return {
        "total_supermarkets": len(_weekly["supermarket"].unique()),
        "total_skus": len(_weekly["sku"].unique()),
        "total_records": int(_weekly["demand"].sum()),
        "total_weekly_rows": len(_weekly),
        "date_min": str(_weekly["week"].min().date()),
        "date_max": str(_weekly["week"].max().date()),
        "num_series": len(series),
        "sku_list": sorted(_weekly["sku"].unique().tolist()),
        "market_list": sorted(_weekly["supermarket"].unique().tolist()),
    }
