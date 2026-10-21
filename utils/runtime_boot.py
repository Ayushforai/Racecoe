"""Configure historical archive + chat sessions before the app imports historical_db."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def wait_for_postgres(timeout_s: float = 90.0) -> bool:
    from utils.db import connect, database_url

    if not database_url():
        return False
    deadline = time.time() + timeout_s
    last_error = ""
    while time.time() < deadline:
        try:
            with connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as exc:
            last_error = str(exc)
            print(f" [boot] Waiting for Postgres: {last_error}")
            time.sleep(2)
    print(f" [boot] Postgres not reachable: {last_error}")
    return False


def ensure_postgres_archive() -> None:
    from utils.db import apply_schema, connect, reset_backend_cache

    applied = apply_schema(include_pgvector=True)
    print(f" [boot] Schema applied (pgvector={applied.get('pgvector')}).")
    with connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM f1.races").fetchone()
        n = int(row["n"]) if row else 0
    if n > 0:
        print(f" [boot] Postgres archive ready ({n} races).")
        reset_backend_cache()
        return

    print(" [boot] Loading Ergast data into Postgres (first boot)...")
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from load_ergast_to_postgres import DATA_DIR, load_archive
    from utils.historical_archive import ensure_historical_csvs

    if not ensure_historical_csvs(DATA_DIR):
        raise RuntimeError(
            "Historical CSV files are missing and could not be downloaded automatically."
        )

    counts = load_archive(DATA_DIR, apply=False)
    print(f" [boot] Postgres archive load complete: {counts.get('f1.races', 0)} races.")
    reset_backend_cache()


def configure_data_backend(*, postgres_timeout_s: float = 90.0) -> str:
    """
    Pick CSV vs Postgres for historical lookups and chat sessions.

    When DATABASE_URL is set and Postgres is reachable, applies schema, loads f1.*
    if empty, and sets HISTORICAL_BACKEND=postgres. Otherwise uses in-repo CSVs.

    Returns a short label for logs: "postgres" or "csv".
    """
    url = (os.getenv("DATABASE_URL") or "").strip()
    if url and wait_for_postgres(timeout_s=postgres_timeout_s):
        os.environ.setdefault("HISTORICAL_BACKEND", "postgres")
        os.environ.setdefault("SESSION_STORE", "postgres")
        try:
            ensure_postgres_archive()
            return "postgres"
        except Exception as exc:
            print(f" [boot] Postgres archive setup failed ({exc}); falling back to CSV.")
            os.environ["HISTORICAL_BACKEND"] = "csv"
            os.environ["SESSION_STORE"] = "memory"
            return "csv"

    print(" [boot] No Postgres; using CSV archive and in-memory sessions.")
    os.environ["HISTORICAL_BACKEND"] = "csv"
    os.environ["SESSION_STORE"] = "memory"
    return "csv"
