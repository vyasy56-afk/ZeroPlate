"""Owner menu management tests using an isolated temporary SQLite database."""

import os
import tempfile
import unittest
from unittest.mock import patch

import app.database as database
from app import create_app


class FakeForecaster:
    def predict_item(self, **kwargs):
        return {
            "predicted_demand": 84,
            "recommended_cook_qty": 91,
            "safety_buffer_units": 7,
        }


class OwnerMenuTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "owner-menu-test.db")
        self.db_patch = patch.object(database, "DB_PATH", self.db_path)
        self.db_patch.start()

        self.app = create_app()
        self.app.config.update(TESTING=True, OWNER_PASSWORD="test-owner-password")
        self.client = self.app.test_client()

    def tearDown(self):
        self.db_patch.stop()
        self.temp_dir.cleanup()

    def login(self):
        return self.client.post(
            "/owner/login",
            data={"password": "test-owner-password"},
            follow_redirects=True,
        )

    def test_owner_pages_require_login(self):
        response = self.client.get("/owner/menu")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/owner/login", response.headers["Location"])

        response = self.client.get("/owner/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Owner password", response.data)

    def test_owner_can_add_edit_hide_and_plan_a_dish(self):
        self.login()

        dish_form = {
            "name": "Demo Veg Pulao",
            "category": "Rice Specialties",
            "meal_type": "Lunch",
            "base_price": "95",
            "prep_cost": "42",
            "shelf_life_hours": "5",
            "image_emoji": "🍚",
            "base_demand": "84",
        }
        response = self.client.post("/owner/menu/add", data=dish_form, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Demo Veg Pulao", response.data)

        conn = database.get_db_connection()
        item = conn.execute(
            "SELECT * FROM menu_items WHERE name = ?",
            ("Demo Veg Pulao",),
        ).fetchone()
        conn.close()
        self.assertIsNotNone(item)

        with patch("app.routes.owner.get_forecaster", return_value=FakeForecaster()):
            response = self.client.post(
                f"/owner/menu/{item['id']}/plan",
                follow_redirects=True,
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Demand forecast created", response.data)

        conn = database.get_db_connection()
        plan = conn.execute(
            "SELECT * FROM daily_plans WHERE item_id = ?",
            (item["id"],),
        ).fetchone()
        self.assertIsNotNone(plan)
        self.assertEqual(plan["predicted_demand"], 84)
        self.assertEqual(plan["recommended_cook_qty"], 91)
        self.assertEqual(plan["status"], "PLANNED")
        conn.close()

        with patch("app.routes.owner.get_forecaster", return_value=FakeForecaster()):
            self.client.post(f"/owner/menu/{item['id']}/plan")
        conn = database.get_db_connection()
        plan_count = conn.execute(
            "SELECT COUNT(*) FROM daily_plans WHERE item_id = ?",
            (item["id"],),
        ).fetchone()[0]
        conn.close()
        self.assertEqual(plan_count, 1)

        edited = dict(dish_form)
        edited["base_price"] = "105"
        self.client.post(f"/owner/menu/{item['id']}/update", data=edited)
        conn = database.get_db_connection()
        updated = conn.execute(
            "SELECT base_price FROM menu_items WHERE id = ?",
            (item["id"],),
        ).fetchone()
        conn.close()
        self.assertEqual(updated["base_price"], 105)

        self.client.post(f"/owner/menu/{item['id']}/toggle")
        conn = database.get_db_connection()
        hidden = conn.execute(
            "SELECT is_active FROM menu_items WHERE id = ?",
            (item["id"],),
        ).fetchone()
        conn.close()
        self.assertEqual(hidden["is_active"], 0)


if __name__ == "__main__":
    unittest.main()
