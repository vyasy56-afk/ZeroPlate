"""
ZeroPlate: Mentor Demo Data Loader

Creates one deterministic sample operating day for a project demonstration.
The loader:
- Uses the trained demand model to create menu forecasts.
- Adds kitchen preparation and sales records.
- Creates active discounted-meal listings and example reservations.
- Adds NGO donations in pending, claimed, collected and composted states.
- Adds compost records for the recovery dashboard.

Safety:
- Does not delete or overwrite existing records.
- Refuses to seed a date that already has daily plans.
- Uses a single SQLite transaction so a failed run is rolled back.
- Uses clearly labelled DEMO reservation IDs and tokens.
"""

import argparse
import os
import sys
from datetime import date, datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.database import get_db_connection, init_db
from models.predict import get_forecaster


DEMO_WEATHER_C = 23.5
DEMO_RAINFALL_MM = 2.0
DEMO_SIMULATED_TIME = "19:45"
DEMO_DISCOUNT_PCT = 55
DEMO_FACILITY = "Main Compost Facility / Green Digester Unit 2"

# Sales shares are fixed so every run produces the same easy-to-explain example.
SALES_SHARE_BY_ITEM = {
    101: 0.90,  # Rajma Chawal
    102: 0.87,  # Paneer Thali
    103: 0.72,  # Dal Makhani
    104: 0.86,  # Veg Biryani
    105: 0.88,  # Chole Bhature
    106: 0.91,  # Masala Dosa
    107: 0.79,  # Samosa Plate
    108: 0.92,  # Aloo Paratha
    109: 0.81,  # Cold Coffee
    110: 0.84,  # Gulab Jamun
}

# These four items are shown in the discounted-meal marketplace.
MARKETPLACE_DEMOS = {
    103: {"reserved_qty": 2, "student": "Aarav Mehta", "student_id": "DEMO-1021", "order_status": "COLLECTED"},
    107: {"reserved_qty": 1, "student": "Meera Joshi", "student_id": "DEMO-1047", "order_status": "RESERVED"},
    109: {"reserved_qty": 2, "student": "Kabir Singh", "student_id": "DEMO-1083", "order_status": "RESERVED"},
    110: {"reserved_qty": 1, "student": "Anaya Rawat", "student_id": "DEMO-1106", "order_status": "RESERVED"},
}

# The same sample day shows different recovery outcomes for the mentor.
DONATION_DEMOS = {
    101: {"status": "PENDING_CLAIM", "ngo_index": None, "claimed_at": None, "collected_at": None, "pin": "4821"},
    102: {"status": "CLAIMED", "ngo_index": 1, "claimed_at": "19:20", "collected_at": None, "pin": "2468"},
    104: {"status": "COLLECTED", "ngo_index": 2, "claimed_at": "18:55", "collected_at": "19:20", "pin": "1357"},
    106: {"status": "EXPIRED_TO_COMPOST", "ngo_index": 0, "claimed_at": None, "collected_at": None, "pin": "8642"},
}


def _closing_time(meal_type):
    if meal_type in ("Breakfast", "Lunch"):
        return "19:30"
    if meal_type == "Snacks":
        return "20:30"
    return "21:00"


def _insert_compost_record(cursor, *, plan_id, item_name, weight_kg, reason, logged_at, batch_code):
    weight_kg = round(float(weight_kg), 2)
    cursor.execute(
        """
        INSERT INTO composting_logs
        (daily_plan_id, item_name, weight_kg, source_reason, facility_partner,
         estimated_compost_kg, co2_diverted_kg, logged_at, batch_code)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            plan_id,
            item_name,
            weight_kg,
            reason,
            DEMO_FACILITY,
            round(weight_kg * 0.45, 2),
            round(weight_kg * 2.5, 2),
            logged_at,
            batch_code,
        ),
    )


def seed_operational_day(sim_date=None, sim_time=DEMO_SIMULATED_TIME):
    """Seed a mentor-ready sample day without deleting existing application data."""
    init_db()
    sim_date = sim_date or date.today().isoformat()
    parsed_date = datetime.strptime(sim_date, "%Y-%m-%d")
    day_of_week = parsed_date.weekday()
    is_weekend = 1 if day_of_week in (5, 6) else 0
    date_key = parsed_date.strftime("%Y%m%d")

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        existing_count = cursor.execute(
            "SELECT COUNT(*) FROM daily_plans WHERE date = ?",
            (sim_date,),
        ).fetchone()[0]

        if existing_count:
            print(
                f"No changes made: {existing_count} daily plan(s) already exist for {sim_date}. "
                "Choose another date with --date YYYY-MM-DD if you need a separate demo day."
            )
            return False

        items = cursor.execute("SELECT * FROM menu_items ORDER BY id").fetchall()
        if not items:
            raise RuntimeError("No menu items are configured. Run database initialization first.")

        ngos = cursor.execute(
            "SELECT id, name FROM ngos WHERE verified = 1 ORDER BY id"
        ).fetchall()
        if len(ngos) < 3:
            raise RuntimeError("At least three verified demo NGO partners are required.")

        forecaster = get_forecaster()
        predictions = {}
        for item in items:
            prediction = forecaster.predict_item(
                item_id=item["id"],
                meal_type=item["meal_type"],
                category=item["category"],
                day_of_week=day_of_week,
                is_weekend=is_weekend,
                is_holiday=0,
                is_exam_day=0,
                temperature_c=DEMO_WEATHER_C,
                rainfall_mm=DEMO_RAINFALL_MM,
                trend_7d=max(25.0, item["base_price"] * 1.5),
                trend_14d=max(25.0, item["base_price"] * 1.5),
                is_promoted=1 if item["id"] == 104 else 0,
                safety_buffer_pct=0.08,
            )
            predictions[item["id"]] = prediction

        # Start one transaction only after all model predictions are ready.
        cursor.execute("BEGIN IMMEDIATE")

        cursor.execute(
            """
            UPDATE contextual_settings
            SET simulated_date = ?, simulated_time = ?, day_of_week = ?,
                is_holiday = 0, is_exam_day = 0, temperature_c = ?,
                rainfall_mm = ?, closing_window_mins = 90,
                active_canteen_name = 'Main Canteen'
            WHERE id = 1
            """,
            (sim_date, sim_time, day_of_week, DEMO_WEATHER_C, DEMO_RAINFALL_MM),
        )

        plans_by_item = {}
        for item in items:
            item_id = item["id"]
            prediction = predictions[item_id]
            predicted = int(prediction["predicted_demand"])
            recommended = int(prediction["recommended_cook_qty"])
            prepared = recommended

            sales_share = SALES_SHARE_BY_ITEM.get(item_id, 0.84)
            sold = min(prepared - 1, max(0, int(round(prepared * sales_share))))
            remaining = prepared - sold

            if item_id in MARKETPLACE_DEMOS:
                status = "SURPLUS_DETECTED"
            elif item_id in DONATION_DEMOS:
                status = "CLOSED"
            else:
                status = "CLOSED" if item["meal_type"] in ("Breakfast", "Lunch") else "IN_SERVICE"

            cursor.execute(
                """
                INSERT INTO daily_plans
                (date, item_id, predicted_demand, recommended_cook_qty,
                 actual_prepared_qty, actual_sold_qty, status, safety_buffer,
                 threshold_surplus, closing_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 8, ?)
                """,
                (
                    sim_date,
                    item_id,
                    predicted,
                    recommended,
                    prepared,
                    sold,
                    status,
                    recommended - predicted,
                    _closing_time(item["meal_type"]),
                ),
            )
            plans_by_item[item_id] = {
                "plan_id": cursor.lastrowid,
                "item": item,
                "remaining": remaining,
            }

        # Active discounted listings plus example student reservations.
        marketplace_count = 0
        order_count = 0
        for item_id, demo in MARKETPLACE_DEMOS.items():
            plan_data = plans_by_item.get(item_id)
            if not plan_data:
                continue

            item = plan_data["item"]
            available_to_list = plan_data["remaining"]
            reserved = min(demo["reserved_qty"], max(0, available_to_list - 1))
            if available_to_list <= 1:
                continue

            original_price = float(item["base_price"])
            discounted_price = round(original_price * (1 - DEMO_DISCOUNT_PCT / 100), 0)
            cursor.execute(
                """
                INSERT INTO marketplace_items
                (daily_plan_id, title, description, original_price, discounted_price,
                 discount_pct, quantity_listed, quantity_claimed, status, listed_at, pickup_until)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?)
                """,
                (
                    plan_data["plan_id"],
                    item["name"] + " - demo offer",
                    f"Sample mentor-demo listing for {item['name']}. Available at a {DEMO_DISCOUNT_PCT}% discount.",
                    original_price,
                    discounted_price,
                    DEMO_DISCOUNT_PCT,
                    available_to_list,
                    reserved,
                    "19:10",
                    _closing_time(item["meal_type"]),
                ),
            )
            listing_id = cursor.lastrowid
            marketplace_count += 1

            if reserved:
                cursor.execute(
                    """
                    INSERT INTO marketplace_orders
                    (marketplace_item_id, student_name, student_id_roll, quantity,
                     total_price, token_code, status, ordered_at, collected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        listing_id,
                        demo["student"],
                        demo["student_id"],
                        reserved,
                        round(discounted_price * reserved, 2),
                        f"DEMO-ZP-{date_key}-{item_id}",
                        demo["order_status"],
                        "19:25",
                        "19:40" if demo["order_status"] == "COLLECTED" else None,
                    ),
                )
                order_count += 1

        # NGO donation examples: awaiting assignment, assigned, collected and composted.
        donation_ids = {}
        for item_id, demo in DONATION_DEMOS.items():
            plan_data = plans_by_item.get(item_id)
            if not plan_data:
                continue

            ngo_id = ngos[demo["ngo_index"]]["id"] if demo["ngo_index"] is not None else None
            deadline = "20:45" if demo["status"] == "PENDING_CLAIM" else "20:30"
            cursor.execute(
                """
                INSERT INTO ngo_donations
                (daily_plan_id, item_name, portions, ngo_id, pickup_window_deadline,
                 status, dispatched_at, claimed_at, collected_at, verification_pin, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan_data["plan_id"],
                    plan_data["item"]["name"],
                    plan_data["remaining"],
                    ngo_id,
                    deadline,
                    demo["status"],
                    "19:45",
                    demo["claimed_at"],
                    demo["collected_at"],
                    demo["pin"],
                    "Illustrative sample record created for a mentor demonstration.",
                ),
            )
            donation_ids[item_id] = cursor.lastrowid

        # Compost examples include one expired donation and kitchen preparation scraps.
        compost_count = 0
        expired_item = plans_by_item.get(106)
        if expired_item and 106 in donation_ids:
            _insert_compost_record(
                cursor,
                plan_id=expired_item["plan_id"],
                item_name=expired_item["item"]["name"] + " - uncollected donation",
                weight_kg=expired_item["remaining"] * 0.35,
                reason="EXPIRED_UNCOLLECTED_NGO",
                logged_at="21:10",
                batch_code=f"DEMO-CMP-{date_key}-001",
            )
            compost_count += 1

        for suffix, item_name, weight, logged_at in [
            ("002", "Vegetable peelings and kitchen trimmings", 4.8, "14:15"),
            ("003", "Mixed salad and preparation scraps", 3.2, "15:30"),
        ]:
            _insert_compost_record(
                cursor,
                plan_id=None,
                item_name=item_name,
                weight_kg=weight,
                reason="KITCHEN_SCRAPS",
                logged_at=logged_at,
                batch_code=f"DEMO-CMP-{date_key}-{suffix}",
            )
            compost_count += 1

        conn.commit()

        print("\nZeroPlate mentor demo data loaded successfully.")
        print(f"Demo date: {sim_date} | Simulated time: {sim_time}")
        print(f"Menu plans: {len(plans_by_item)}")
        print(f"Active discounted listings: {marketplace_count}")
        print(f"Example reservations: {order_count}")
        print(f"Donation records: {len(donation_ids)}")
        print(f"Compost batches: {compost_count}")
        if 102 in donation_ids:
            print(f"Demo PIN for claimed donation #{donation_ids[102]}: 2468")
        print("\nOpen these pages during your demonstration:")
        print("  Overview:     http://127.0.0.1:5000/")
        print("  Forecast:     http://127.0.0.1:5000/forecast")
        print("  Kitchen:      http://127.0.0.1:5000/production")
        print("  Marketplace:  http://127.0.0.1:5000/marketplace")
        print("  Donations:    http://127.0.0.1:5000/ngo")
        print("  Compost:      http://127.0.0.1:5000/composting")
        print("  Analytics:    http://127.0.0.1:5000/analytics")
        print("\nNOTE: These are illustrative sample records, not live canteen transactions.")
        return True

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Load ZeroPlate mentor demo data.")
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Demo date in YYYY-MM-DD format (defaults to today's date).",
    )
    parser.add_argument(
        "--time",
        default=DEMO_SIMULATED_TIME,
        help=f"Demo clock time in HH:MM format (default: {DEMO_SIMULATED_TIME}).",
    )
    args = parser.parse_args()
    datetime.strptime(args.time, "%H:%M")
    seed_operational_day(sim_date=args.date, sim_time=args.time)


if __name__ == "__main__":
    main()
