"""Boot Postgres (schema + archive if empty), then run the FastAPI app.

Used as the Docker / Render CMD so `docker compose up` uses SQL by default.
Falls back to CSV + in-memory sessions if DATABASE_URL is unset or unreachable.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")


def main() -> None:
    from utils.runtime_boot import configure_data_backend

    mode = configure_data_backend()
    print(f" [boot] Historical data backend: {mode}")

    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("server:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
