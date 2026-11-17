"""
ZeroPlate Database Layer
Provides SQLite database connection, table initialization, and seed data.
Also compatible with MySQL.
"""

import os
import sqlite3
from datetime import datetime, timedelta

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Vercel's function filesystem is read-only except for /tmp. SQLite data there
# is ephemeral per serverless instance. Locally, persist the DB under data/.
DB_PATH = os.environ.get("DATABASE_PATH") or (
    "/tmp/zeroplate.db" if os.environ.get("VERCEL") else
    os.path.join(_PROJECT_ROOT, "data", "zeroplate.db")
)


def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        meal_type TEXT NOT NULL,
        base_price REAL NOT NULL,
        prep_cost REAL NOT NULL,
        shelf_life_hours INTEGER NOT NULL DEFAULT 6,
        image_emoji TEXT DEFAULT '🍲'
    );

    CREATE TABLE IF NOT EXISTS daily_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        item_id INTEGER NOT NULL,
        predicted_demand INTEGER NOT NULL,
        recommended_cook_qty INTEGER NOT NULL,
        actual_prepared_qty INTEGER NOT NULL,
        actual_sold_qty INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'IN_SERVICE', -- PLANNED, COOKING, IN_SERVICE, SURPLUS_DETECTED, CLOSED
        safety_buffer INTEGER NOT NULL DEFAULT 0,
        threshold_surplus INTEGER NOT NULL DEFAULT 8,
        closing_time TEXT NOT NULL DEFAULT '20:30',
        FOREIGN KEY (item_id) REFERENCES menu_items(id)
    );

    CREATE TABLE IF NOT EXISTS marketplace_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        daily_plan_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        original_price REAL NOT NULL,
        discounted_price REAL NOT NULL,
        discount_pct INTEGER NOT NULL,
        quantity_listed INTEGER NOT NULL,
        quantity_claimed INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, SOLD_OUT, EXPIRED_TO_NGO
        listed_at TEXT NOT NULL,
        pickup_until TEXT NOT NULL,
        FOREIGN KEY (daily_plan_id) REFERENCES daily_plans(id)
    );

    CREATE TABLE IF NOT EXISTS marketplace_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        marketplace_item_id INTEGER NOT NULL,
        student_name TEXT NOT NULL,
        student_id_roll TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        total_price REAL NOT NULL,
        token_code TEXT NOT NULL UNIQUE,
        status TEXT NOT NULL DEFAULT 'RESERVED', -- RESERVED, COLLECTED, CANCELLED
        ordered_at TEXT NOT NULL,
        collected_at TEXT,
        FOREIGN KEY (marketplace_item_id) REFERENCES marketplace_items(id)
    );

    CREATE TABLE IF NOT EXISTS ngos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        registration_no TEXT NOT NULL,
        contact_person TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT NOT NULL,
        address TEXT NOT NULL,
        verified INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS ngo_donations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        daily_plan_id INTEGER,
        item_name TEXT NOT NULL,
        portions INTEGER NOT NULL,
        ngo_id INTEGER,
        pickup_window_deadline TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING_CLAIM', -- PENDING_CLAIM, CLAIMED, COLLECTED, EXPIRED_TO_COMPOST
        dispatched_at TEXT NOT NULL,
        claimed_at TEXT,
        collected_at TEXT,
        verification_pin TEXT,
        notes TEXT,
        FOREIGN KEY (daily_plan_id) REFERENCES daily_plans(id),
        FOREIGN KEY (ngo_id) REFERENCES ngos(id)
    );

    CREATE TABLE IF NOT EXISTS composting_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        daily_plan_id INTEGER,
        item_name TEXT NOT NULL,
        weight_kg REAL NOT NULL,
        source_reason TEXT NOT NULL, -- EXPIRED_UNCOLLECTED_NGO, QUALITY_SAFETY_THRESHOLD, KITCHEN_SCRAPS
        facility_partner TEXT NOT NULL,
        estimated_compost_kg REAL NOT NULL,
        co2_diverted_kg REAL NOT NULL,
        logged_at TEXT NOT NULL,
        batch_code TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS contextual_settings (
        id INTEGER PRIMARY KEY,
        simulated_date TEXT NOT NULL,
        simulated_time TEXT NOT NULL,
        day_of_week INTEGER NOT NULL,
        is_holiday INTEGER NOT NULL DEFAULT 0,
        is_exam_day INTEGER NOT NULL DEFAULT 0,
        temperature_c REAL NOT NULL DEFAULT 24.0,
        rainfall_mm REAL NOT NULL DEFAULT 0.0,
        closing_window_mins INTEGER NOT NULL DEFAULT 90,
        active_canteen_name TEXT NOT NULL DEFAULT 'Graphic Era Central Canteen'
    );
    """)

    conn.commit()

    # Seed verified NGOs if empty
    cursor.execute("SELECT COUNT(*) FROM ngos")
    if cursor.fetchone()[0] == 0:
        ngos_seed = [
            ("Robin Hood Army (Dehradun Chapter)", "RHA-DDN-2021", "Arun Negi", "+91 98971 23456", "dehradun@robinhoodarmy.com", "Rajpur Road, Dehradun", 1),
            ("Feeding India by Zomato (GEU Volunteers)", "FI-UK-8821", "Pooja Rawat", "+91 97600 45678", "contact@feedingindia.org", "Subhash Nagar, Clement Town, Dehradun", 1),
            ("Wasteless Smiles Foundation", "WSF-DDN-4412", "Dr. Manoj Joshi", "+91 94120 78901", "support@wasteless-smiles.org", "Patel Nagar, Dehradun", 1)
        ]
        cursor.executemany("""
            INSERT INTO ngos (name, registration_no, contact_person, phone, email, address, verified)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ngos_seed)
        conn.commit()

    # Seed menu items if empty
    cursor.execute("SELECT COUNT(*) FROM menu_items")
    if cursor.fetchone()[0] == 0:
        items_seed = [
            (101, "Rajma Chawal", "Main Course", "Lunch", 80.0, 35.0, 6, "🍛"),
            (102, "Paneer Butter Masala Thali", "Thali", "Lunch", 130.0, 55.0, 5, "🍱"),
            (103, "Dal Makhani & Naan Combo", "Main Course", "Dinner", 110.0, 48.0, 6, "🫓"),
            (104, "Veg Dum Biryani", "Rice Specialties", "Lunch", 120.0, 50.0, 5, "🍚"),
            (105, "Chole Bhature", "North Indian", "Breakfast", 70.0, 30.0, 4, "🥟"),
            (106, "Masala Dosa with Sambar", "South Indian", "Breakfast", 65.0, 26.0, 4, "🥞"),
            (107, "Crispy Samosa Plate (2 pcs)", "Quick Bites", "Snacks", 30.0, 12.0, 8, "🥟"),
            (108, "Aloo Paratha with Curd", "Breakfast", "Breakfast", 50.0, 20.0, 4, "🫓"),
            (109, "Cold Coffee Shake", "Beverages", "Snacks", 45.0, 18.0, 12, "🥤"),
            (110, "Gulab Jamun (2 pcs)", "Desserts", "Dinner", 40.0, 15.0, 24, "🍯")
        ]
        cursor.executemany("""
            INSERT INTO menu_items (id, name, category, meal_type, base_price, prep_cost, shelf_life_hours, image_emoji)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, items_seed)
        conn.commit()

    # Seed simulation state
    cursor.execute("SELECT COUNT(*) FROM contextual_settings")
    if cursor.fetchone()[0] == 0:
        now = datetime.now()
        cursor.execute("""
            INSERT INTO contextual_settings (id, simulated_date, simulated_time, day_of_week, is_holiday, is_exam_day, temperature_c, rainfall_mm, closing_window_mins, active_canteen_name)
            VALUES (1, ?, '18:45', 2, 0, 1, 26.5, 0.0, 90, 'Graphic Era Central Canteen')
        """, (now.strftime("%Y-%m-%d"),))
        conn.commit()

    conn.close()

if __name__ == "__main__":
    init_db()
    print("ZeroPlate database initialized successfully at:", DB_PATH)
