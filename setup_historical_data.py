"""CLI entry point: ensure data/historical_csvs exists (same logic as server auto-bootstrap)."""

from pathlib import Path

from utils.historical_archive import ensure_historical_csvs

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "historical_csvs"


def setup_kaggle_data() -> None:
    if ensure_historical_csvs(DATA_DIR, allow_download=True):
        print(f"Success! Historical CSVs are stored in: {DATA_DIR}")
    else:
        raise SystemExit(
            "Could not download historical CSVs. Configure Kaggle credentials "
            "(https://www.kaggle.com/settings/api) or set KAGGLE_API_TOKEN, then retry."
        )


if __name__ == "__main__":
    setup_kaggle_data()
