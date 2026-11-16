"""
ZeroPlate: Seed Demo Data Generator
Initializes a rich, operational day for demonstration:
- Generates ML predictions for today's menu
- Creates daily production plans
- Simulates realistic sales progression
- Triggers Tier 1 (Marketplace), Tier 2 (NGO), and Tier 3 (Composting)
"""

import os
import sys
import random
from datetime import datetime

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.database import get_db_connection, init_db
from models.predict import get_forecaster
from app.escalation_engine import run_escalation_cycle

def seed_operational_day(sim_date="2026-11-16", sim_time="19:45"):
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Update or insert contextual settings
    # Nov 16, 2026: Exam period at Graphic Era, 23.5°C, light evening drizzle
    cursor.execute("""
        UPDATE contextual_settings SET
            simulated_date = ?,
            simulated_time = ?,
            day_of_week = 0,
            is_holiday = 0,
            is_exam_day = 1,
            temperature_c = 23.5,
            rainfall_mm = 2.0,
            closing_window_mins = 90
        WHERE id = 1
    """, (sim_date, sim_time))
    conn.commit()

    # Clear old plans for this date to start fresh
    cursor.execute("DELETE FROM daily_plans WHERE date = ?", (sim_date,))
    cursor.execute("DELETE FROM marketplace_items")
    cursor.execute("DELETE FROM marketplace_orders")
    cursor.execute("DELETE FROM ngo_donations")
    cursor.execute("DELETE FROM composting_logs")
    conn.commit()

    forecaster = get_forecaster()
    items = cursor.execute("SELECT * FROM menu_items").fetchall()

    plans_created = []
    for item in items:
        # Contextual inputs
        pred_res = forecaster.predict_item(
            item_id=item["id"],
            meal_type=item["meal_type"],
            category=item["category"],
            day_of_week=0,
            is_weekend=0,
            is_holiday=0,
            is_exam_day=1, # Graphic Era exam week
            temperature_c=23.5,
            rainfall_mm=2.0,
            trend_7d=item["base_price"] * 1.5,
            trend_14d=item["base_price"] * 1.5,
            is_promoted=1 if item["id"] == 104 else 0, # Biryani promoted
            safety_buffer_pct=0.08
        )

        pred_demand = pred_res["predicted_demand"]
        recommended_qty = pred_res["recommended_cook_qty"]
        # Kitchen prepared the recommended quantity (Prevention Before Cure)
        prepared_qty = recommended_qty

        # Simulate sales progression at 19:45
        # For dinner items (closing at 21:00): in active service
        # For lunch items (closing at 19:30): already closed and escalated!
        if item["meal_type"] in ["Lunch", "Breakfast"]:
            closing_time = "19:30"
            # 85-95% sold, leaving a small surplus
            sold_qty = int(round(prepared_qty * random.uniform(0.84, 0.92)))
        elif item["meal_type"] == "Snacks":
            closing_time = "20:30"
            sold_qty = int(round(prepared_qty * random.uniform(0.78, 0.88)))
        else: # Dinner
            closing_time = "21:00"
            sold_qty = int(round(prepared_qty * random.uniform(0.65, 0.75)))

        cursor.execute("""
            INSERT INTO daily_plans 
            (date, item_id, predicted_demand, recommended_cook_qty, actual_prepared_qty, actual_sold_qty, status, safety_buffer, threshold_surplus, closing_time)
            VALUES (?, ?, ?, ?, ?, ?, 'IN_SERVICE', ?, 8, ?)
        """, (
            sim_date,
            item["id"],
            pred_demand,
            recommended_qty,
            prepared_qty,
            sold_qty,
            recommended_qty - pred_demand,
            closing_time
        ))
        plans_created.append(item["name"])

    conn.commit()
    conn.close()

    print(f"Daily plans generated for {len(plans_created)} menu items.")
    print("Running escalation engine cycle at simulated time:", sim_time)
    res = run_escalation_cycle()
    print("Escalation actions executed:", len(res["actions"]))
    for act in res["actions"]:
        print(" -", act)

    # Add a couple of student orders for realism
    conn = get_db_connection()
    cursor = conn.cursor()
    active_mk = cursor.execute("SELECT * FROM marketplace_items WHERE status = 'ACTIVE' LIMIT 2").fetchall()
    student_names = [("Aman Sharma", "GEU/2024/BCADS/042"), ("Sneha Verma", "GEU/2023/BTECH/118")]
    for idx, mk in enumerate(active_mk):
        if idx < len(student_names):
            name, roll = student_names[idx]
            token = f"ZP-TK-{random.randint(1000, 9999)}"
            cursor.execute("""
                INSERT INTO marketplace_orders 
                (marketplace_item_id, student_name, student_id_roll, quantity, total_price, token_code, status, ordered_at)
                VALUES (?, ?, ?, 1, ?, ?, 'RESERVED', '19:25')
            """, (mk["id"], name, roll, mk["discounted_price"], token))
            cursor.execute("""
                UPDATE marketplace_items SET quantity_claimed = quantity_claimed + 1 WHERE id = ?
            """, (mk["id"],))
    conn.commit()

    # Also add a couple historical composting records so the module is immediately rich
    cursor.execute("SELECT COUNT(*) FROM composting_logs")
    if cursor.fetchone()[0] < 3:
        past_compost = [
            ("Chole Bhature (Trim & Prep)", 4.2, "KITCHEN_SCRAPS", "Graphic Era Campus Bio-Compost Facility / Green Digester Unit 2", 1.89, 10.5, "14:15", "CMP-20261116-001"),
            ("Mixed Salad & Vegetable Peelings", 6.8, "KITCHEN_SCRAPS", "Graphic Era Campus Bio-Compost Facility / Green Digester Unit 2", 3.06, 17.0, "15:30", "CMP-20261116-002")
        ]
        cursor.executemany("""
            INSERT INTO composting_logs (item_name, weight_kg, source_reason, facility_partner, estimated_compost_kg, co2_diverted_kg, logged_at, batch_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, past_compost)
        conn.commit()

    conn.close()
    print("ZeroPlate demo environment seeded successfully!")

if __name__ == "__main__":
    seed_operational_day()
