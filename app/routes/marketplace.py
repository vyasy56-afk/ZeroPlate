"""
ZeroPlate: Student Marketplace Routes
Module 3: Student Marketplace for Discounted Surplus
Enables pupils and local community to purchase discounted "Surprise Boxes"
near canteen closing time, preventing food waste before it happens.
"""

from flask import Blueprint, render_template, request
from app.database import get_db_connection

marketplace_bp = Blueprint("marketplace", __name__, url_prefix="/marketplace")

@marketplace_bp.route("/")
def index():
    conn = get_db_connection()
    settings = conn.execute("SELECT * FROM contextual_settings WHERE id = 1").fetchone()

    # Active surprise listings
    listings = conn.execute("""
        SELECT mi.*, dp.actual_prepared_qty, dp.actual_sold_qty, dp.closing_time, 
               m.name as original_item_name, m.image_emoji, m.category, m.meal_type
        FROM marketplace_items mi
        JOIN daily_plans dp ON mi.daily_plan_id = dp.id
        JOIN menu_items m ON dp.item_id = m.id
        WHERE mi.status = 'ACTIVE'
        ORDER BY mi.discount_pct DESC
    """).fetchall()

    conn.close()

    return render_template("marketplace.html", 
                           settings=settings, 
                           listings=listings)
