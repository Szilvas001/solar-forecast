"""Console-script entry points for Solar Forecast.

The individual runner scripts are named ``01_download_cams.py`` etc. so they can
be executed directly as ``python scripts/01_download_cams.py``. Those file names
are not valid Python module identifiers (they start with a digit), so the
``sf-*`` console commands exposed by ``pyproject.toml`` delegate through this
module.
"""

from __future__ import annotations

import sys
from importlib import import_module


def _run(module_name: str, argv: list[str] | None = None) -> int:
    module = import_module(f"scripts.{module_name}")
    if argv is not None:
        sys.argv = ["sf-"] + argv
    return module.main() or 0


def download_cams(argv: list[str] | None = None) -> int:
    """``sf-download`` — download CAMS training history."""
    return _run("01_download_cams", argv)


def train_kt_model(argv: list[str] | None = None) -> int:
    """``sf-train`` — train the XGBoost Kt model."""
    return _run("02_train_kt_model", argv)


def run_dashboard(argv: list[str] | None = None) -> int:
    """``sf-dashboard`` — start the Streamlit dashboard."""
    return _run("03_run_dashboard", argv)


def generate_demo_model(argv: list[str] | None = None) -> int:
    """``sf-demo-model`` — generate a synthetic demo Kt model."""
    return _run("04_generate_demo_model", argv)
