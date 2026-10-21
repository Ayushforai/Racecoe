"""Initialize a hosted Postgres (Render, Neon, Supabase): schema + Ergast archive.

Run once from your laptop with DATABASE_URL in .env pointing at the cloud database.
The production container runs the same logic automatically on first boot.

  cp .env.example .env   # set DATABASE_URL=...
  python scripts/bootstrap_hosted_db.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import os

os.chdir(ROOT)

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from utils.db import database_url, health_payload
from utils.runtime_boot import ensure_postgres_archive, wait_for_postgres


def main() -> int:
    if not database_url():
        print(
            "Set DATABASE_URL in .env to your hosted Postgres connection string "
            "(Render, Neon, or Supabase)."
        )
        return 1
    print("Connecting to hosted Postgres...")
    if not wait_for_postgres(timeout_s=120.0):
        print("Could not reach Postgres. Check URL, firewall, and SSL (sslmode=require).")
        return 1
    ensure_postgres_archive()
    payload = health_payload()
    rows = payload.get("archive_rows")
    print(f"Done. archive_rows={rows}, historical_using_postgres={payload.get('historical_using_postgres')}")
    if not rows:
        print("Warning: f1.races is still empty — check logs above.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
