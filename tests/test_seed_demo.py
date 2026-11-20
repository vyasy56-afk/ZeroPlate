"""Tests for the safe mentor demo data loader."""

import os
import tempfile
import unittest
from unittest.mock import patch

import app.database as database
from app.seed_demo import seed_operational_day


class StubForecaster:
    """Small predictable replacement for the saved ML models in seed tests."""

    def predict_item(self, **kwargs):
        return {
            "predicted_demand": 100,
            "recommended_cook_qty": 108,
            "rf_prediction": 99.0,
            "gb_prediction": 100.0,
            "safety_buffer_units": 8,
            "model_used": "Test forecaster",
        }


class MentorDemoSeedTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(self.temp_dir.name, "zeroplate-test.db")
        self.db_path_patch = patch.object(database, "DB_PATH", self.database_path)
        self.db_path_patch.start()
        database.init_db()

    def tearDown(self):
        self.db_path_patch.stop()
        self.temp_dir.cleanup()

    def test_seed_creates_all_demo_sections_and_is_safe_to_repeat(self):
        with patch("app.seed_demo.get_forecaster", return_value=StubForecaster()):
            first_run = seed_operational_day("2026-11-20", "19:45")
            second_run = seed_operational_day("2026-11-20", "19:45")

        self.assertTrue(first_run)
        self.assertFalse(second_run)

        conn = database.get_db_connection()
        try:
            self.assertEqual(
                conn.execute("SELECT COUNT(*) FROM daily_plans WHERE date = '2026-11-20'").fetchone()[0],
                10,
            )
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM marketplace_items").fetchone()[0], 4)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM marketplace_orders").fetchone()[0], 4)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM ngo_donations").fetchone()[0], 4)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM composting_logs").fetchone()[0], 3)

            statuses = {
                row["status"]
                for row in conn.execute("SELECT status FROM ngo_donations").fetchall()
            }
            self.assertEqual(
                statuses,
                {"PENDING_CLAIM", "CLAIMED", "COLLECTED", "EXPIRED_TO_COMPOST"},
            )
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
