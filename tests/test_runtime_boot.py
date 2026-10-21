import os
import unittest
from unittest.mock import patch

from utils.db import reset_backend_cache
from utils.runtime_boot import configure_data_backend


class TestRuntimeBoot(unittest.TestCase):
    def tearDown(self):
        reset_backend_cache()

    def test_no_database_url_defaults_to_csv(self):
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in {"DATABASE_URL", "HISTORICAL_BACKEND", "SESSION_STORE"}
        }
        with patch.dict(os.environ, env, clear=True):
            mode = configure_data_backend(postgres_timeout_s=0.1)
            backend = os.environ.get("HISTORICAL_BACKEND")
        self.assertEqual(mode, "csv")
        self.assertEqual(backend, "csv")


if __name__ == "__main__":
    unittest.main()
