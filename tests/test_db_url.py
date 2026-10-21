import unittest

from utils.db import normalize_database_url


class TestDatabaseUrl(unittest.TestCase):
    def test_postgres_scheme_normalized(self):
        self.assertTrue(
            normalize_database_url("postgres://u:p@h/db").startswith("postgresql://")
        )

    def test_neon_gets_sslmode(self):
        url = normalize_database_url("postgresql://u:p@ep-x.us-east-2.aws.neon.tech/neondb")
        self.assertIn("sslmode=require", url)


if __name__ == "__main__":
    unittest.main()
