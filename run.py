#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "").lower() in ("1", "true", "yes")

    app.run(host=host, port=port, debug=debug)
