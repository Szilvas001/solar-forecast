"""Load demo-data/demo_forecast_budapest.csv into the local PostgreSQL server.

Creates (if missing) the `solar_forecast` database and the `demo_forecast`
table, then upserts every row keyed on the UTC timestamp so the load is
idempotent. Connection params come from environment variables with sensible
defaults matching the rest of this project:
    PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE_ADMIN
Set PGPASSWORD before running (python scripts/load_demo_to_postgres.py).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd
import psycopg2

log = logging.getLogger("load_demo_to_postgres")

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "demo-data" / "demo_forecast_budapest.csv"

ADMIN_DB = os.getenv("PGDATABASE_ADMIN", "postgres")
TARGET_DB = os.getenv("PGDATABASE", "solar_forecast")
HOST = os.getenv("PGHOST", "localhost")
PORT = int(os.getenv("PGPORT", "5432"))
USER = os.getenv("PGUSER", "postgres")
PASSWORD = os.getenv("PGPASSWORD", "")

DDL = """
CREATE TABLE IF NOT EXISTS demo_forecast (
    utc_timestamp        TIMESTAMPTZ NOT NULL,
    ghi_wm2              DOUBLE PRECISION,
    ghi_clearsky_wm2     DOUBLE PRECISION,
    power_kw             DOUBLE PRECISION,
    energy_kwh           DOUBLE PRECISION,
    clearness_kt         DOUBLE PRECISION,
    cell_temp_c          DOUBLE PRECISION,
    source_file          TEXT NOT NULL,
    ingested_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (utc_timestamp)
);
"""


def _connect(dbname: str, autocommit: bool = False):
    conn = psycopg2.connect(
        host=HOST,
        port=PORT,
        dbname=dbname,
        user=USER,
        password=PASSWORD,
    )
    if autocommit:
        conn.autocommit = True
    return conn


def ensure_database() -> None:
    """Create the target database if it does not exist yet."""
    conn = _connect(ADMIN_DB, autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TARGET_DB,))
            if cur.fetchone() is None:
                cur.execute(f"CREATE DATABASE \"{TARGET_DB}\" ENCODING 'UTF8'")
                log.info("created database %s", TARGET_DB)
            else:
                log.info("database %s already exists", TARGET_DB)
    finally:
        conn.close()


def load_csv() -> tuple[int, int]:
    df = pd.read_csv(CSV_PATH)
    df["utc_timestamp"] = pd.to_datetime(df["timestamp_utc"], utc=True)
    df = df.drop(columns=["timestamp_utc"])
    df["source_file"] = CSV_PATH.name

    cols = list(df.columns)
    ph = ", ".join(["%s"] * len(cols))
    col_names = ", ".join(cols)
    update_cols = [c for c in cols if c not in ("utc_timestamp", "source_file")]
    update_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)

    insert = (
        f"INSERT INTO demo_forecast ({col_names}) VALUES ({ph}) "
        f"ON CONFLICT (utc_timestamp) DO UPDATE SET {update_clause}"
    )

    records = [
        tuple(
            None if pd.isna(v) else v.isoformat() if isinstance(v, pd.Timestamp) else v
            for v in row
        )
        for row in df.itertuples(index=False, name=None)
    ]

    with _connect(TARGET_DB) as conn:
        with conn.cursor() as cur:
            cur.execute(DDL)
            cur.executemany(insert, records)
        conn.commit()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM demo_forecast")
            total = cur.fetchone()[0]
    return len(records), total


def print_preview() -> None:
    with _connect(TARGET_DB) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT utc_timestamp, ghi_wm2, power_kw, clearness_kt, "
            "cell_temp_c FROM demo_forecast ORDER BY utc_timestamp "
            "LIMIT 5"
        )
        rows = cur.fetchall()
    print("Latest 5 rows (ascending):")
    for r in rows:
        print("  ", r)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if not PASSWORD:
        log.warning("PGPASSWORD is empty - set it before running if auth fails.")
    ensure_database()
    inserted, total = load_csv()
    print(
        f"Upserted {inserted} rows from {CSV_PATH.name} into "
        f"database '{TARGET_DB}'.table 'demo_forecast'."
    )
    print(f"Total rows now in table: {total}")
    print_preview()


if __name__ == "__main__":
    main()
