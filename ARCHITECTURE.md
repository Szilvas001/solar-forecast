# Architecture

This document describes the architecture and key commands for this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt
# or install as editable package
pip install -e .

# Run tests
pytest

# Run a single test
pytest tests/test_api.py::test_health

# Start Streamlit dashboard (http://localhost:8501)
./run.sh

# Start FastAPI backend (http://localhost:8000, docs at /docs)
./run.sh --api

# Start both services
./run.sh --all

# Docker (recommended for production)
cp .env.example .env
docker compose up -d

# One-off CAMS fetch (requires CAMS_API_KEY or ~/.cdsapirc)
python -m solar_forecast.cams_fetcher [--config path/to/config.yaml] [--dry-run]

# Install automated CAMS fetch cron (10:15 and 22:15 UTC)
python -c "from solar_forecast.cams_fetcher.scheduler import setup_cron; setup_cron()"

# Advanced: download CAMS training data (requires CAMS_API_KEY)
python scripts/01_download_cams.py --start 2021-01-01 --end 2024-12-31

# Advanced: train XGBoost Kt model
python scripts/02_train_kt_model.py
```

## Architecture

This is a physics-based + AI hybrid solar PV production forecasting system. It has three entry points: a Streamlit dashboard, a FastAPI REST API, and direct Python usage via `run_demo_forecast()`.

### Forecast Pipeline

The single entry point for all forecasts is `run_demo_forecast()` in `solar_forecast/demo/pipeline.py`. The pipeline runs these steps in order:

1. **Open-Meteo weather** — fetches live hourly GHI/DNI/DHI/cloud cover/temperature (free, no key)
2. **CAMS atmosphere** (`_resolve_atmosphere`) — pulls per-timestep AOD, Ångström exponents α₁/α₂, SSA, asymmetry, ozone, precipitable water, surface pressure, BLH from PostgreSQL if available; falls back to continental-Europe climatology constants otherwise
3. **SPECTRL2 clear-sky** (`solar_forecast/clearsky/spectrl2_model.py`) — pvlib Bird & Riordan spectral model, parameterised with CAMS-derived atmospheric state; falls back to `simplified_solis` if it fails
4. **Physics Kt** (`solar_forecast/allsky/physics_kt.py`) — Delta-Eddington two-stream approximation with per-timestep CAMS AOD, SSA, asymmetry
5. **Optional AI Kt** (`solar_forecast/allsky/ai_trainer.py`) — XGBoost model (21 features, trained on CAMS data); blended as `0.4 × Kt_phys + 0.6 × Kt_ai`
6. **Perez transposition** — GHI/DNI/DHI → POA irradiance on the tilted panel surface
7. **IAM correction** (`solar_forecast/production/iam_model.py`) — ASHRAE, Martin-Ruiz, or Fresnel angle-of-incidence models
8. **NOCT cell temperature** — `T_cell = T_air + (NOCT − 20) / 800 × G_POA`
9. **DC → AC power** — temperature coefficient + system losses (inverter × wiring × soiling)

For sub-hourly real-time estimates, `run_realtime_forecast()` in the same file runs the identical physics stack at configurable resolution (5–60 min) over a short horizon (1–72 h), returning a smooth continuous curve and the current-moment power value.

The `AllSkyModel` class in `solar_forecast/allsky/hybrid_model.py` wraps steps 4–5 as an orchestrator; `physics_weight` config key (`α`) controls the blend (default 0.40).

### AI modules

Two independent ML modules exist:

- **`solar_forecast/allsky/ai_trainer.py`** — `KtTrainer`: XGBoost regressor on 21 atmospheric features (AOD, SSA, BLH, PM2.5, cloud, …). Requires CAMS training data. Saved to `models/kt_xgb.joblib`.
- **`solar_forecast/allsky/historical_trainer.py`** — `HistoricalGHITrainer`: lighter gradient-boosted model that learns `GHI_obs = f(GHI_clear, cloud_cover, time encodings)`. Works with Open-Meteo history alone. Performance contract enforced at training time: **R² ≥ 0.75, RMSE ≤ 10 % of peak**. Falls back to sklearn `HistGradientBoostingRegressor` if XGBoost is absent.

### CAMS Fetcher

`solar_forecast/cams_fetcher/` is the integrated version of the standalone `cams-fetcher` tool. Key modules:

- `client.py` — thin cdsapi wrapper (lazy import; reads `CADS_URL`/`CADS_KEY` or `~/.cdsapirc`)
- `grib_processor.py` — GRIB decode + bilinear interpolation to target lat/lon (lazy pygrib import)
- `db.py` — PostgreSQL upsert layer (lazy psycopg2); also exposes `read_latest_forecast()` for the forecast pipeline
- `runner.py` — `run_once()` orchestrates download → parse → insert; entry point for CLI (`python -m solar_forecast.cams_fetcher`)
- `scheduler.py` — `CamsScheduler` (daemon thread, sleeps until next run) + `setup_cron()` (installs crontab entries)
- `config_default.yaml` — default variables: total column ozone, water vapour, AOD at 469/550/670/865/1240 nm, BLH, T2m, surface pressure, 5 speciated AODs

The data bridge `solar_forecast/data_ingestion/cams_query.py` reads CAMS data from PostgreSQL into forecast-pipeline-friendly units, computes Ångström exponents from multi-wavelength AODs, and mixes SSA/asymmetry from speciated AODs.

### Service Layer

- **FastAPI** (`app/api/main.py`) — three routers: `health`, `locations`, `forecast`
  - `POST /forecast` — one-off forecast by coordinates
  - `GET /forecast/{location_id}` — forecast for a saved location, results cached in SQLite by date
  - `POST /forecast/realtime` — sub-hourly real-time curve (5–60 min resolution, 1–72 h horizon)
  - `GET /export/csv` — CSV download of a cached forecast
- **Streamlit** (`solar_forecast/dashboard/app.py`) — seven tabs: Dashboard, Real-Time, Forecast, Locations, Reports, Settings, Model Training
  - Three user-level tiers in sidebar: **Basic** (city + kW), **Pro** (tilt/azimuth/horizon/CSV), **Expert** (SR upload, IAM, AI toggle)
  - Real-Time tab: auto-refreshes every 60 s, shows smooth sub-hourly curve, NOW marker, Kt and cell-temperature sub-charts, atmospheric diagnostics
- Both the dashboard and the API call `run_demo_forecast()` / `run_realtime_forecast()` directly

### Data Storage

- **SQLite** (`data/solar_forecast.db`, WAL mode) — `app/db/sqlite_manager.py` manages two tables:
  - `locations` — saved PV system configurations
  - `forecasts` — daily cached forecast results (upsert keyed by `location_id + forecast_date`)
- **PostgreSQL** — two roles: (a) CAMS atmospheric data via `solar_forecast/cams_fetcher/db.py`; (b) training data via `solar_forecast/data_ingestion/db_manager.py`
- **Models** — XGBoost Kt model at `models/kt_xgb.joblib`; HistoricalGHITrainer at `models/ghi_historical.joblib` (when trained)

### Configuration

- `config.yaml` — all non-secret settings (location defaults, PV system parameters, model paths, CAMS date ranges)
- `.env` — secrets and overrides (`CAMS_API_KEY`/`CADS_KEY`, `PGPASSWORD`, `DEMO_MODE`); loaded automatically by `python-dotenv`
- `solar_forecast/cams_fetcher/config_default.yaml` — CAMS dataset/variable/schedule configuration
- Key defaults: `tilt=None` auto-computes as `abs(lat) × 0.76`; `azimuth=None` defaults to 180° south

### Testing

`tests/conftest.py` monkeypatches `sqlite_manager.DB_PATH` to a temporary file for every test. API tests mock `run_demo_forecast()` / `run_realtime_forecast()` to avoid live network calls. Physics tests patch `_fetch_openmeteo` to return an empty DataFrame and verify graceful clear-sky fallback. `test_historical_trainer.py` validates the R² ≥ 0.75 / RMSE ≤ 10 % accuracy contract on synthetic data.
