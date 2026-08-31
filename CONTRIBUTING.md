# Contributing to Solar Forecast

Thanks for taking the time to contribute! Here is how to work on this project.

## Development environment

Requires **Python 3.10+**.

```bash
# Clone and create a virtualenv
git clone https://github.com/Szilvas001/solar-forecast.git
cd solar-forecast
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
# source .venv/bin/activate

# Install the package in editable mode with dev tools
pip install -e ".[dev]"
```

## Code style

The project uses [ruff](https://github.com/astral-sh/ruff) for linting and
formatting. Configuration lives in `pyproject.toml`.

```bash
# Check formatting
ruff format --check .

# Lint
ruff check .

# Auto-fix what can be fixed
ruff check . --fix
```

## Running tests

```bash
# Fast suite (unit + API tests, no network)
pytest -m "not slow"

# Everything, including slow physics tests
pytest
```

Tests must be green before a PR is merged. CI runs the same commands on
Python 3.10 / 3.11 / 3.12.

## Branching & pull requests

1. Branch from `main`: `git checkout -b feature/my-change`
2. Make changes, keeping commits focused and atomic.
3. Update `CHANGELOG.md` if the change is user-facing.
4. Run `ruff` and `pytest` locally.
5. Push and open a pull request against `main`. Use the PR template.

## Commit messages

Keep messages short and imperative, e.g.:

- `Add CI pipeline for lint and tests`
- `Fix Ångström exponent sign in cams_query`
- `Bump API version to 2.2.0`

## Project layout

```
solar_forecast/   # Core physics + AI engine (importable package)
app/              # FastAPI REST backend + SQLite manager
scripts/          # CLI entry points (also exposed as sf-* commands)
tests/            # pytest suite
docs/             # User-facing documentation
demo-data/        # Offline demo CSV
```

## Reporting issues

Use the issue templates. Include your environment, a minimal repro, and the
relevant log output.