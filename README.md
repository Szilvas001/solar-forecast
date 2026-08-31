# ☀️ Solar Forecast

> **Physics-based + AI hybrid photovoltaic (PV) production forecasting platform.**

A production-grade, fully containerised system that predicts solar energy output
for any location in seconds. It blends a **physics engine** (spectral clear-sky
models, aerosol optics, transposition) with an optional **XGBoost AI correction**
to produce accurate hourly PV forecasts, exposed through a **Streamlit dashboard**
and a **FastAPI REST API**.

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?logo=python&logoColor=white)
![CI](https://img.shields.io/github/actions/workflow/status/Szilvas001/solar-forecast/ci.yml?branch=main&label=CI&logo=github)
[![License](https://img.shields.io/badge/License-Proprietary-blue.svg)](LICENSE.txt)

</div>

---

## Highlights

- **Runs with zero configuration** in demo mode — no API keys, no database, no trained model.
- **Physics-first**: pvlib `spectrl2` clear-sky, Ångström / Hänel aerosol physics, Perez transposition, NOCT cell-temperature and SR/IAM integration.
- **Optional AI layer**: XGBoost `Kt` correction (21 atmospheric features) and a lightweight `GHI` gradient-boosted model with an enforced accuracy contract (R² ≥ 0.75).
- **Live weather**: free Open-Meteo integration (no key), plus **CAMS** atmospheric enrichment when configured.
- **Two UIs**: an interactive Streamlit SaaS dashboard and a documented FastAPI backend with Swagger UI.
- **Tested**: pytest suite (unit + API + physics smoke tests) and CI on Python 3.10–3.12.
- **Modern tooling**: packaging via `pyproject.toml`, linting/formatting with ruff, Docker support.

---

## Quick start

### Docker (recommended)

```bash
git clone https://github.com/Szilvas001/solar-forecast.git
cd solar-forecast
cp .env.example .env
docker compose up
```

Open the dashboard at **http://localhost:8501** and the API docs at **http://localhost:8000/docs**.

### Manual (local Python)

```bash
python -m venv .venv && .venv\Scripts\activate   # Windows
# source .venv/bin/activate                      # Linux/macOS
pip install -e ".[dev]"

# Run the 60-second smoke check (compile + unit tests, no network)
pytest -m "not slow"

# Start what you need
sf-dashboard            # Streamlit UI  → http://localhost:8501
sf-train                # train the demo AI model
uvicorn app.api.main:app --reload    # FastAPI → http://localhost:8000
```
---

## REST API (FastAPI)

| Method | Endpoint                | Description                                        |
|--------|-------------------------|----------------------------------------------------|
| `GET`  | `/health`               | Service health, version, engine                    |
| `POST` | `/forecast`             | One-off forecast by coordinates / PV params        |
| `GET`  | `/forecast/{location_id}` | Forecast for a saved location (cached in SQLite) |
| `POST` | `/forecast/realtime`    | Sub-hourly real-time curve (5–60 min resolution)   |
| `GET`  | `/locations`            | List locations (paginated + search)                |
| `POST` | `/locations`            | Register a PV system location                      |
| `GET`  | `/model/versions`       | Registered ML model versions                       |
| `GET`  | `/ingestion/status`     | Data ingestion status (CAMS / Open-Meteo)          |

```bash
curl -X POST http://localhost:8000/forecast \
  -H "Content-Type: application/json" \
  -d '{"lat": 47.5, "lon": 19.0, "capacity_kw": 5.0, "horizon_days": 7}'
```

Interactive docs: **http://localhost:8000/docs** (Swagger) and `/redoc`.

---

## Architecture

High-level data flow — every forecast runs through one pipeline entry point,
`run_demo_forecast()` in `solar_forecast/demo/pipeline.py`:

```
Open-Meteo weather ─┐
CAMS atmosphere ────┼─► SPECTRL2 clear-sky ─► Physics Kt ─► [AI Kt (opt.)]
                    │                              │
                    └─► Perez transposition ─► IAM ─► cell temp ─► DC→AC power
```

1. **Weather** — live hourly GHI / DNI / DHI / cloud / temperature (Open-Meteo).
2. **Atmosphere** (optional) — AOD, Ångström α₁/α₂, SSA, ozone, water vapour from PostgreSQL (CAMS); falls back to climatology constants.
3. **Clear sky** — pvlib `spectrl2` (Bird & Riordan), parameterised by atmospheric state.
4. **All-sky Kt** — Delta-Eddington two-stream approximation; blended with the AI model.
5. **AI** (optional) — XGBoost catches residual cloud / aerosol error; blend α defaults to 0.60 AI.
6. **Transposition & conversion** — Perez, ASHRAE / Martin-Ruiz / Fresnel IAM, NOCT cell temperature, DC→AC losses.

Two independent front-ends (Streamlit dashboard, FastAPI) both call the same
pipeline, so physics guarantees are identical across UIs.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full module-level breakdown.
---

## Project layout

```
solar_forecast/          # Core importable package (physics + AI engine)
  ├── physics/           #   Ångström, Hänel, SSA, aerosol optics
  ├── clearsky/          #   pvlib spectrl2 clear-sky irradiance
  ├── allsky/            #   Kt physics model + XGBoost / GHI trainers
  ├── production/        #   SR curves, IAM, PV power conversion
  ├── cams_fetcher/      #   CAMS downloader + PostgreSQL layer
  ├── data_ingestion/    #   CAMS query / Open-Meteo clients
  ├── demo/              #   Demo pipeline (no keys needed)
  └── dashboard/         #   Streamlit SaaS UI
app/
  ├── api/               #   FastAPI REST backend (routes, schemas)
  └── db/                #   SQLite location manager
scripts/                  # CLI entry points ── exposed as sf-* commands
tests/                    pytest suite
docs/                     user-facing documentation
demo-data/                offline demo CSV
Dockerfile · docker-compose.yml · pyproject.toml · config.yaml
```

---

## Testing & quality

| Tool   | Command                     | Purpose                          |
|--------|-----------------------------|----------------------------------|
| pytest | `pytest -m "not slow"`      | Fast unit + API tests            |
| pytest | `pytest`                    | Full suite incl. physics         |
| ruff   | `ruff check .`              | Linting                          |
| ruff   | `ruff format --check .`     | Formatting check                 |

CI (`.github/workflows/ci.yml`) runs lint + tests on **Python 3.10 / 3.11 / 3.12**
for every push and pull request.

---

## Documentation

| Doc | Content |
|---|---|
| [Installation](docs/installation.md) | Docker + manual install |
| [Quickstart](docs/quickstart.md) | First forecast in minutes |
| [Configuration](docs/configuration.md) | `config.yaml` / `.env` reference |
| [API reference](docs/api.md) | All REST endpoints & schemas |
| [Dashboard](docs/dashboard.md) | Streamlit UI guide |
| [Data pipeline](docs/data_pipeline.md) | Weather ingestion internals |
| [Training](docs/training.md) | CAMS + XGBoost advanced training |
| [Troubleshooting](docs/troubleshooting.md) | Common issues |
| [Contributing](CONTRIBUTING.md) | Development guide |

---

## Roadmap

- [ ] Coverage reporting integrated into CI
- [ ] `ruff` pre-commit hooks
- [ ] Full CAMS/Open-Meteo e2e fixtures in tests
- [ ] Model explainability endpoint (SHAP)

---

## License

See [LICENSE.txt](LICENSE.txt). Third-party: pvlib (BSD), XGBoost (Apache-2.0),
FastAPI (MIT), Streamlit (Apache-2.0).