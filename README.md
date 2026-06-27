# Demand Forecast AI

A production-ready demand forecasting dashboard for retail SKU×supermarket demand prediction, built with Dash (Plotly), FastAPI-flavored Flask REST endpoints, and optimized for Azure App Service deployment.

## Architecture

- **Frontend**: Dash (Plotly) multi-page application with indigo/slate design system
- **Backend**: Flask server with REST API endpoints hosted on the same Dash server
- **Models**: LightGBM (ONNX) and Prophet pre-trained models (lazy-loaded on first use)
- **Deployment**: Docker container → Azure App Service (Basic/Standard plans)

## Project Structure

```
├── app/
│   ├── main.py              # Dash app + Flask server bootstrap
│   ├── routes/              # REST API endpoints (health, forecast)
│   ├── services/            # Business logic (data, forecast, insights)
│   ├── utils/               # Configuration, data loading utilities
│   ├── components/          # Reusable UI components (sidebar, KPI cards, charts, tables)
│   ├── pages/               # 4-page Dash application
│   └── assets/              # Static CSS and JS
├── saved_models/
│   ├── demand_forecast_inference.py  # Standalone inference module
│   ├── lgbm_h1.onnx … lgbm_h8.onnx  # LightGBM ONNX models
│   ├── lgbm_meta.json               # Model metadata and feature columns
│   └── prophet/                     # Prophet pickle models + index
├── demand.csv               # Historical daily demand data
├── promotions.csv           # Promotion calendar data
├── Dockerfile               # Azure-ready container image
├── requirements.txt         # Minimal Python dependencies
├── run.py                   # Development startup script
└── .env.example             # Environment variable template
```

## Pages

1. **Dashboard** — KPI cards (3 supermarkets, 3 SKUs, total records, date range) + overview charts
2. **Forecast Explorer** — Select SKU×market×model, simulate promotion weeks (8 toggles), generate forecast with interactive Plotly chart + prediction details panel
3. **Analytics** — 3 tabs: Historical Analysis (trends, heatmap, seasonality, YoY), Promotion Analysis (lift, distribution, stats), Model Comparison (LightGBM vs Prophet side-by-side)
4. **Business Insights** — Auto-computed insights (highest SKU/market, average demand, promotion uplift %, seasonality peaks/troughs, trend direction)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check (uptime, data/models loaded) |
| `GET` | `/api/forecast?sku=&market=&ref_week=&model=&is_promo=` | Generate 8-week forecast |

## Quick Start

### Prerequisites

- Python 3.12+
- Docker (for containerized deployment)

### Local Development

```bash
pip install -r requirements.txt

# Place demand.csv and promotions.csv in the project root
# Place model files in saved_models/
python run.py
```

Open http://localhost:8000 in your browser.

### Docker Deployment

```bash
# Place data files and models first, then:
docker build -t demand-forecast .
docker run -p 8000:8000 demand-forecast
```

### Azure App Service Deployment

1. Build the Docker image and push to Azure Container Registry
2. Create an App Service with Docker Compose or Container deployment
3. Set environment variables in App Service Configuration:
   - `PORT=8000`
   - No other configuration required

## Models

Two pre-trained models are included:

- **LightGBM (ONNX)**: 8 direct multi-step models (one per horizon week). Uses calendar features, lags (4,8,13,26,52 weeks), rolling statistics, and entity dummies. Runs via ONNX Runtime — no LightGBM Python package required.

- **Prophet**: 9 per-series models with yearly seasonality and promotion regressor. Provides point forecasts with upper/lower confidence intervals.

Models are lazy-loaded on first forecast request for fast container startup (<5 seconds).

## Design

- **Color palette**: Indigo (`#4F46E5`) primary, slate neutrals, green/amber/red accents
- **Typography**: System font stack (-apple-system, Segoe UI, Roboto, sans-serif) — zero external requests
- **Dark mode**: CSS variable swap via theme toggle
- **Responsive**: CSS Grid + Flexbox with breakpoints at 768px and 1024px
- **Charts**: All Plotly with zoom, pan, hover, and PNG export

## Performance Optimizations

- Data loaded once at application startup (never reloaded)
- Models lazy-loaded on first use (reused for all subsequent requests)
- No external CDN dependencies (fonts, icons, libraries)
- Minimal Python dependencies (no scikit-learn, statsmodels, or heavy ML frameworks)
- Console logging only (Azure captures stdout/stderr automatically)
- Docker image based on `python:3.12-slim` (~1.2GB compressed)

## License

MIT
