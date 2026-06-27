from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
MODELS_DIR = Path(os.getenv("MODELS_DIR", str(BASE_DIR / "saved_models")))

DEMAND_CSV = DATA_DIR / "demand.csv"
PROMOTIONS_CSV = DATA_DIR / "promotions.csv"
INFERENCE_MODULE = MODELS_DIR / "demand_forecast_inference.py"

LGBM_META = MODELS_DIR / "lgbm_meta.json"
PROPHET_DIR = MODELS_DIR / "prophet"

HORIZON = 8

SKUS = ["Free Range Eggs", "Organic Milk", "Whole Wheat Bread"]
MARKETS = ["DailyNeeds", "FreshMart", "GreenBasket"]

TRAINING_ORIGIN = "2019-01-07"
