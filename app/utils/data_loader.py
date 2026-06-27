import pandas as pd
import numpy as np
from pathlib import Path
from app.utils.config import SKUS, MARKETS, TRAINING_ORIGIN


def load_demand(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], format="mixed", dayfirst=True)
    df = _winsorise(df)
    df = _fill_missing(df)
    return df


def load_promotions(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["promotion_date"] = pd.to_datetime(
        df["promotion_date"], format="mixed", dayfirst=True
    )
    return df


def build_weekly(demand: pd.DataFrame, promotions: pd.DataFrame) -> pd.DataFrame:
    results = []
    for (sku, market), group in demand.groupby(["sku", "supermarket"]):
        g = group.set_index("date").sort_index()
        weekly = g.resample("W-MON")["demand"].sum().reset_index()
        weekly["sku"] = sku
        weekly["supermarket"] = market
        results.append(weekly)
    weekly = pd.concat(results, ignore_index=True).rename(columns={"date": "week"})
    weekly = _add_promo_flags(weekly, promotions)
    return weekly


def get_series_list(weekly: pd.DataFrame) -> list:
    series = sorted(
        weekly[["sku", "supermarket"]].drop_duplicates().to_records(index=False).tolist()
    )
    return [(s, m) for s, m in series]


def _winsorise(df: pd.DataFrame) -> pd.DataFrame:
    cap = df.groupby(["sku", "supermarket"])["demand"].transform(
        lambda x: x.quantile(0.99)
    )
    df = df.copy()
    df["demand"] = df["demand"].clip(upper=cap)
    return df


def _fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["sku", "supermarket", "date"])
    df["demand"] = df.groupby(["sku", "supermarket"])["demand"].transform(
        lambda x: x.ffill().bfill()
    )
    return df


def _add_promo_flags(weekly: pd.DataFrame, promotions: pd.DataFrame) -> pd.DataFrame:
    weekly = weekly.copy()
    weekly["is_promo"] = 0
    for _, row in promotions.iterrows():
        start = row["promotion_date"]
        end = start + pd.Timedelta(days=6)
        mask = (
            (weekly["sku"] == row["sku"])
            & (weekly["supermarket"] == row["supermarket"])
            & (weekly["week"] >= start)
            & (weekly["week"] <= end)
        )
        weekly.loc[mask, "is_promo"] = 1
    return weekly


def get_reference_weeks(weekly: pd.DataFrame) -> list:
    all_mondays = sorted(weekly["week"].dropna().unique())
    if len(all_mondays) >= 8:
        return [str(d.date()) for d in all_mondays[:-7]]
    return [str(d.date()) for d in all_mondays]
