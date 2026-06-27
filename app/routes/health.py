import time
import logging
from flask import Blueprint, jsonify

logger = logging.getLogger("demand-forecast.api")

health_bp = Blueprint("health", __name__)

_start_time = time.time()
_ready = {"data": False, "models": False}


def mark_data_ready():
    _ready["data"] = True


def mark_models_ready():
    _ready["models"] = True


@health_bp.route("/api/health")
def health_check():
    return jsonify({
        "status": "healthy" if all(_ready.values()) else "starting",
        "uptime_seconds": round(time.time() - _start_time, 1),
        "data_loaded": _ready["data"],
        "models_loaded": _ready["models"],
    })
