"""Ensure Ergast historical CSVs exist under data/historical_csvs (auto-download when missing)."""

from __future__ import annotations

import os
import shutil
import threading
from pathlib import Path

KAGGLE_DATASET = "rohanrao/formula-1-world-championship-1950-2020"

# Files read by utils.historical_db._load_historical_csvs
REQUIRED_CSV_FILES = (
    "races.csv",
    "circuits.csv",
    "drivers.csv",
    "constructors.csv",
    "results.csv",
    "status.csv",
    "lap_times.csv",
    "qualifying.csv",
    "sprint_results.csv",
    "driver_standings.csv",
)

# Not in the classic Kaggle bundle; empty Ergast-shaped header is enough for lookups.
_SUPPLEMENT_HEADERS: dict[str, str] = {
    "sprint_results.csv": (
        "resultId,raceId,driverId,constructorId,number,grid,position,positionText,"
        "positionOrder,points,laps,time,milliseconds,fastestLap,fastestLapTime,statusId"
    ),
}

_download_lock = threading.Lock()


def historical_csvs_present(data_dir: Path) -> bool:
    return all((data_dir / name).is_file() for name in REQUIRED_CSV_FILES)


def auto_download_enabled() -> bool:
    raw = (os.getenv("F1_AUTO_DOWNLOAD_HISTORICAL") or "1").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    if os.getenv("PYTEST_CURRENT_TEST"):
        return False
    return True


def _write_supplements(data_dir: Path) -> None:
    for name, header in _SUPPLEMENT_HEADERS.items():
        path = data_dir / name
        if not path.is_file():
            path.write_text(header + "\n", encoding="utf-8")


def download_historical_csvs(data_dir: Path) -> None:
    """Download the Kaggle Ergast dump into data_dir (requires Kaggle API credentials)."""
    import kagglehub

    data_dir.mkdir(parents=True, exist_ok=True)
    cache_path = kagglehub.dataset_download(KAGGLE_DATASET)
    for entry in os.listdir(cache_path):
        src = os.path.join(cache_path, entry)
        if os.path.isfile(src):
            shutil.copy2(src, data_dir / entry)
    _write_supplements(data_dir)


def ensure_historical_csvs(data_dir: Path, *, allow_download: bool | None = None) -> bool:
    """
    Return True when all required CSV files are on disk.
    When allow_download is True (default from F1_AUTO_DOWNLOAD_HISTORICAL), fetches from Kaggle once.
    """
    if historical_csvs_present(data_dir):
        return True

    if allow_download is None:
        allow_download = auto_download_enabled()
    if not allow_download:
        return False

    with _download_lock:
        if historical_csvs_present(data_dir):
            return True
        print(
            f" [historical] CSV archive missing under {data_dir}; "
            "downloading Ergast data from Kaggle (one-time)..."
        )
        try:
            download_historical_csvs(data_dir)
        except Exception as exc:
            print(f" [historical] Auto-download failed: {exc}")
            return False
        ok = historical_csvs_present(data_dir)
        if ok:
            print(f" [historical] CSV archive ready in {data_dir}.")
        return ok
