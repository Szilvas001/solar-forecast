# Changelog

All notable changes to **AI Solar Production Forecast SaaS** are documented here.

---

## [2.2.0] — 2026-08-31

### Added
- **GitHub Actions CI** (`.github/workflows/ci.yml`) — lint + format (ruff) and the
  pytest suite on Python 3.10 / 3.11 / 3.12 for every push and pull request
- **Community scaffolding** — `CONTRIBUTING.md`, PR template, bug-report and
  feature-request issue templates
- **`scripts/load_demo_to_postgres.py`** — idempotent PostgreSQL loader for the
  bundled demo CSV (creates the `solar_forecast` database and `demo_forecast`
  table if missing, upserts on the primary key)

### Changed
- **Packaging migrated from `setup.py` to `pyproject.toml`** — single source of
  truth for metadata, dependency groups (`cams`, `dev`), console scripts and
  ruff/pytest configuration; `scripts` is now a proper package so the `sf-*`
  entry points install correctly
- **Code style** — repository consistent with **ruff** (lint + format); all
  fixable issues (unused imports, collection calls, exception chaining, ambiguous
  variable names, late-binding closures) cleaned up
- **Version unified to 2.2.0** across `pyproject.toml`, FastAPI metadata,
  `/health`, dashboard and model registry
- **README rewritten** as a portfolio-grade reference — badges, quick start,
  API table, architecture diagram, quality and layout sections

### Fixed
- `raise ... from exc` exception chaining in API routes (`ingestion`, `forecast`,
  `features`, `locations`, `model`)
- Late-binding closure over loop variable in `spectrl2_model` (`_integrate`)
- `.ruff_cache/` added to `.gitignore`

---

## [2.1.0] — 2026-05-03

### Added
- **7-table SQLite schema** — `model_versions` table with ML model registry; 6 performance indexes on CAMS/OM/ingestion/forecast/model_versions tables
- **`GET /model/status`** — returns loaded model files, versions, and training metrics from DB
- **`GET /model/versions`** — paginated model version history by type (`kt_xgb`, `ghi_historical`)
- **Pagination on `GET /locations`** — `page`, `per_page`, `search` query params; response is `PaginatedLocations`
- **`ConfidenceOut` in every `ForecastOut`** — `confidence_pct`, `confidence_label` (High/Medium/Low), `confidence_reasons` list
- **`iam_model` and `denorm_factor` in `ForecastRequest`** — full SR/IAM/denorm control via API
- **`spectral_mm` and `iam` fields in `HourlyPoint`** — spectral mismatch factor and IAM correction per timestep
- **`energy_kwh = power_kw × timestep_hours`** — explicit formula, documented in pipeline and API schema
- **Audit log wired** — every `POST /forecast` call writes to `forecast_runs`; every ingestion run (backfill + live) writes to `ingestion_runs`
- **Model versioning** — `register_model_version()` called automatically when saving `KtTrainer` or `HistoricalGHITrainer` models
- **API version 2.1.0** — bumped in `/health` response and FastAPI metadata
- **`engine` field in `/health`** — shows `"SPECTRL2 + CAMS + Perez + XGBoost"`

### Changed
- `ForecastRequest` now validates `technology` and `iam_model` against allowed values
- `GET /locations` response schema changed from `list[LocationOut]` to `PaginatedLocations`
- `HourlyPoint.energy_kwh` is now explicitly `power_kw × 1.0` (hourly) instead of a copy
- `RealtimePoint.energy_kwh` is now explicitly `power_kw × (resolution_minutes / 60)`

### Fixed
- Removed duplicate `get_location()` definition in `solar_forecast/db/manager.py`
- `ConfidenceOut` uses `compute_confidence()` (physics-aware) rather than `100 - cloud_loss_pct`

---

## [2.0.0] — 2026-04-25

### Added
- **Full productization** — buyer-friendly SaaS dashboard with 3-tier UX (Basic / Pro / Expert)
- **Demo mode** — works with zero configuration (no CAMS key, no PostgreSQL, no trained model)
- **FastAPI REST backend** — GET /health, POST /forecast, GET/POST /locations, GET /export/csv
- **SQLite multi-location manager** — save unlimited PV sites, automatic schema migration
- **Docker Compose** — `docker compose up` → working dashboard + API in one command
- **install.sh / run.sh** — one-command install and launch for Linux/macOS
- **3-tier user levels** (Basic → Pro → Expert) — complexity hidden until needed
- **Productized dashboard** — tabs: Dashboard / Locations / Forecast / Reports / Settings / Training
- **pytest test suite** — locations CRUD, API schema, pipeline smoke tests, import tests
- **Full /docs** — installation, quickstart, configuration, API reference, training guide, FAQ

### Changed
- Default database changed from PostgreSQL to **SQLite** (PostgreSQL remains optional)
- Dashboard completely rewritten — modern dark SaaS theme, KPI cards, Plotly charts
- All zip archive files removed from repository

### Physics & AI (carried over from 1.x + enhanced)
- spectrl2 clear-sky with full Ångström / Hänel / SSA / asymmetry parameter support
- XGBoost Kt model with 21 atmospheric features (CAMS-backed, optional)
- Perez transposition + ASHRAE/Martin-Ruiz/Fresnel IAM models
- NOCT cell temperature model
- 5 built-in spectral response curves (mono-Si, poly-Si, CdTe, CIGS, HIT)

---

## [1.0.0] — 2024-12-01

### Added
- Initial release: pvlib spectrl2 clear-sky + CAMS atmospheric physics
- XGBoost Kt model training from CAMS EAC4 + solar radiation service
- Basic Streamlit dashboard (Data / Train / Live Forecast tabs)
- PostgreSQL storage for CAMS data
