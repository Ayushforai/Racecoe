import unittest
from unittest.mock import patch

from utils import query_log, result_cache


class TestQueryLog(unittest.TestCase):
    def setUp(self):
        query_log.clear_memory_for_tests()
        self._db = patch("utils.query_log.database_url", return_value="")
        self._db.start()

    def tearDown(self):
        self._db.stop()
        query_log.clear_memory_for_tests()

    def test_records_session_and_route_in_memory(self):
        query_log.record(
            "results of monaco gp 2021?",
            route="historical",
            session_id="sess-1",
            user_id="user-a",
        )
        rows = query_log.memory_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["query"], "results of monaco gp 2021?")
        self.assertEqual(rows[0]["route"], "historical")
        self.assertEqual(rows[0]["session_id"], "sess-1")
        self.assertEqual(rows[0]["user_id"], "user-a")

    def test_skips_empty_query(self):
        query_log.record("  ", route="historical", session_id="sess-1")
        self.assertEqual(query_log.memory_rows(), [])

    def test_bind_fills_ids(self):
        query_log.bind(session_id="s2", user_id="u2")
        query_log.record("who won?", route="historical")
        self.assertEqual(query_log.memory_rows()[0]["session_id"], "s2")
        self.assertEqual(query_log.memory_rows()[0]["user_id"], "u2")


class TestResultCache(unittest.TestCase):
    def setUp(self):
        result_cache.clear_memory_for_tests()
        self._db = patch("utils.result_cache.database_url", return_value="")
        self._db.start()

    def tearDown(self):
        self._db.stop()
        result_cache.clear_memory_for_tests()

    def test_lookup_skips_loader_on_second_call(self):
        calls = {"n": 0}

        def loader():
            calls["n"] += 1
            return {"Year": 2021, "Grand Prix": "Monaco"}

        key = {"year": 2021, "country": "monaco", "location": None}
        first = result_cache.lookup("race_results", key, loader)
        second = result_cache.lookup("race_results", key, loader)
        self.assertEqual(first, second)
        self.assertEqual(calls["n"], 1)

    def test_does_not_cache_error_strings(self):
        calls = {"n": 0}

        def loader():
            calls["n"] += 1
            return "No races found."

        key = {"year": 2021, "country": "nowhere"}
        result_cache.lookup("race_results", key, loader)
        result_cache.lookup("race_results", key, loader)
        self.assertEqual(calls["n"], 2)

    def test_different_venues_are_separate_keys(self):
        result_cache.put(
            "race_results",
            {"year": 2024, "country": "italy", "location": "monza"},
            {"Grand Prix": "Italian"},
            ttl=60,
        )
        miss = result_cache.get(
            "race_results",
            {"year": 2024, "country": "italy", "location": "imola"},
        )
        self.assertIsNone(miss)

    def test_cached_decorator_uses_structured_args(self):
        calls = {"n": 0}

        @result_cache.cached("driver_teams", "year", "driver_ref")
        def fake_teams(year: int, driver_ref: str) -> dict:
            calls["n"] += 1
            return {"Year": year, "Driver": driver_ref, "Teams": [{"Team": "Mercedes"}]}

        fake_teams(2012, "hamilton")
        fake_teams(2012, "hamilton")
        fake_teams(2012, "vettel")
        self.assertEqual(calls["n"], 2)


class TestQueryLogNotUsedAsCache(unittest.TestCase):
    def test_no_answer_lookup_api_on_query_log(self):
        self.assertFalse(hasattr(query_log, "search"))
        self.assertFalse(hasattr(query_log, "similar"))
        self.assertFalse(hasattr(query_log, "get"))


if __name__ == "__main__":
    unittest.main()
