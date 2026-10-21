import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from utils.historical_archive import (
    REQUIRED_CSV_FILES,
    ensure_historical_csvs,
    historical_csvs_present,
)


class TestHistoricalArchive(unittest.TestCase):
    def test_present_when_all_required_files_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            for name in REQUIRED_CSV_FILES:
                (data_dir / name).write_text("x\n", encoding="utf-8")
            self.assertTrue(historical_csvs_present(data_dir))

    def test_missing_without_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self.assertFalse(
                ensure_historical_csvs(data_dir, allow_download=False),
            )

    @patch("utils.historical_archive.download_historical_csvs")
    def test_auto_download_when_allowed(self, mock_download):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)

            def _fake_download(target: Path) -> None:
                for name in REQUIRED_CSV_FILES:
                    (target / name).write_text("col\n1\n", encoding="utf-8")

            mock_download.side_effect = _fake_download
            self.assertTrue(ensure_historical_csvs(data_dir, allow_download=True))
            mock_download.assert_called_once()

    def test_auto_download_disabled_under_pytest(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            prev = os.environ.get("PYTEST_CURRENT_TEST")
            os.environ["PYTEST_CURRENT_TEST"] = "test"
            try:
                self.assertFalse(ensure_historical_csvs(data_dir))
            finally:
                if prev is None:
                    os.environ.pop("PYTEST_CURRENT_TEST", None)
                else:
                    os.environ["PYTEST_CURRENT_TEST"] = prev


if __name__ == "__main__":
    unittest.main()
