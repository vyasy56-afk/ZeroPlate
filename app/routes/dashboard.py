"""
ZeroPlate: Dashboard & Planning Routes
Covers:
- Landing Page (Synopsis alignment, author info, prevention-before-cure loop)
- Module 1: Demand Prediction Dashboard (Contextual regression, live interactive simulator)
- Module 2: Inventory & Production Planning (Kitchen cooking portions, morning prep checklist)
- Simulation Controller: Advance time and trigger real-time escalation
"""

from flask import Blueprint, render_template
from app.database import get_db_connection

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
def index():
    """
    Project Home & Executive Overview
    Connects the synopsis by Yogesh Vyas · BCA (AI & DS) · Graphic Era
    Displays the 5-step operational loop and current live metrics.
    """
    conn = get_db_connection()
    settings = conn.execute("SELECT * FROM contextual_settings WHERE id = 1").fetchone()
    
    # Quick live counts
    active_plans = conn.execute("SELECT COUNT(*) FROM daily_plans WHERE date = ?", (settings["simulated_date"],)).fetchone()[0]
    active_marketplace = conn.execute("SELECT COUNT(*) FROM marketplace_items WHERE status = 'ACTIVE'").fetchone()[0]
    pending_donations = conn.execute("SELECT COUNT(*) FROM ngo_donations WHERE status IN ('PENDING_CLAIM', 'CLAIMED')").fetchone()[0]
    compost_logs_count = conn.execute("SELECT COUNT(*) FROM composting_logs").fetchone()[0]
    
    conn.close()

    return render_template("index.html", 
                           settings=settings, 
                           counts={
                               "plans": active_plans,
                               "marketplace": active_marketplace,
                               "donations": pending_donations,
                               "compost": compost_logs_count
                           })

@dashboard_bp.route("/forecast")
def forecast():
    """
    Module 1: Demand Prediction Dashboard
    - Item-level regression predictions using Random Forest and Gradient Boosting
    - RMSE model evaluation comparison against naive baseline
    - Feature importance breakdown
    - Contextual inputs: Weather, exams, holidays, trends
    """
    conn = get_db_connection()
    settings = conn.execute("SELECT * FROM contextual_settings WHERE id = 1").fetchone()
    menu_items = conn.execute("SELECT * FROM menu_items").fetchall()
    
    daily_plans = conn.execute("""
        SELECT dp.*, mi.name as item_name, mi.category, mi.meal_type, mi.base_price, mi.image_emoji
        FROM daily_plans dp
        JOIN menu_items mi ON dp.item_id = mi.id
        WHERE dp.date = ?
    """, (settings["simulated_date"],)).fetchall()

    conn.close()

    return render_template("forecast.html", 
                           settings=settings, 
                           daily_plans=daily_plans, 
                           menu_items=menu_items)

@dashboard_bp.route("/production")
def production():
    """
    Module 2: Canteen Inventory & Production Planning
    - Translates ML demand forecast into kitchen cooking targets before cooking commences
    - Morning prep checklist
    - Raw ingredient requirement calculator
    - Real-time cooking status tracking
    """
    conn = get_db_connection()
    settings = conn.execute("SELECT * FROM contextual_settings WHERE id = 1").fetchone()
    
    plans = conn.execute("""
        SELECT dp.*, mi.name as item_name, mi.category, mi.meal_type, mi.base_price, mi.prep_cost, mi.image_emoji
        FROM daily_plans dp
        JOIN menu_items mi ON dp.item_id = mi.id
        WHERE dp.date = ?
        ORDER BY mi.meal_type DESC
    """, (settings["simulated_date"],)).fetchall()

    # Ingredient quantity estimates based on planned portions and typical recipe ratios
    total_portions = sum(p["recommended_cook_qty"] for p in plans)
    ingredients = [
        {"name": "Basmati Rice", "qty_kg": round(total_portions * 0.08, 1), "category": "Grains & Rice", "stock_status": "In Stock"},
        {"name": "Whole Wheat Atta & Maida", "qty_kg": round(total_portions * 0.06, 1), "category": "Flour", "stock_status": "In Stock"},
        {"name": "Rajma & Lentils (Dal)", "qty_kg": round(total_portions * 0.05, 1), "category": "Pulses", "stock_status": "In Stock"},
        {"name": "Fresh Paneer (Dairy)", "qty_kg": round(total_portions * 0.04, 1), "category": "Dairy", "stock_status": "Restocked Today"},
        {"name": "Cooking Oil & Pure Ghee", "qty_kg": round(total_portions * 0.025, 1), "category": "Oils & Fats", "stock_status": "In Stock"},
        {"name": "Potatoes, Onions & Tomatoes", "qty_kg": round(total_portions * 0.12, 1), "category": "Fresh Produce", "stock_status": "In Stock"},
        {"name": "Spices & Garam Masala Mix", "qty_kg": round(total_portions * 0.015, 1), "category": "Spices", "stock_status": "In Stock"}
    ]

    conn.close()

    return render_template("production.html", 
                           settings=settings, 
                           plans=plans, 
                           ingredients=ingredients,
                           total_portions=total_portions)

@dashboard_bp.route("/simulation")
def simulation():
    """
    Interactive Simulation and Demonstration Controller
    Enables setting simulated time, testing closing windows,
    triggering Tier 1, Tier 2, and Tier 3 surplus escalations instantly.
    """
    conn = get_db_connection()
    settings = conn.execute("SELECT * FROM contextual_settings WHERE id = 1").fetchone()
    conn.close()
    return render_template("simulation.html", settings=settings)
