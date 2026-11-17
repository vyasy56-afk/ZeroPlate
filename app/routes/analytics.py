"""
ZeroPlate: Operational analytics
Summarises preparation, sales, surplus recovery and compost records for the selected operating day.
"""

from flask import Blueprint, render_template
from app.database import get_db_connection

analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")


@analytics_bp.route("/")
def index():
    conn = get_db_connection()
    settings = conn.execute(
        "SELECT * FROM contextual_settings WHERE id = 1"
    ).fetchone()

    plans = conn.execute("""
        SELECT
            dp.*,
            mi.name AS item_name,
            mi.prep_cost,
            mi.category
        FROM daily_plans dp
        JOIN menu_items mi ON dp.item_id = mi.id
        WHERE dp.date = ?
        ORDER BY mi.name
    """, (settings["simulated_date"],)).fetchall()

    comparison_data = []
    traditional_waste_portions = 0
    current_leftover_portions = 0
    estimated_prep_cost_avoided = 0.0

    for plan in plans:
        # This is a comparison estimate, not a measured historical baseline:
        # traditional preparation is modelled as 25% above predicted demand.
        traditional_prep = int(round(plan["predicted_demand"] * 1.25))
        sold = plan["actual_sold_qty"]
        prepared = plan["actual_prepared_qty"]
        traditional_leftover = max(0, traditional_prep - sold)
        current_leftover = max(0, prepared - sold)
        avoided_prep_units = max(0, traditional_prep - prepared)

        traditional_waste_portions += traditional_leftover
        current_leftover_portions += current_leftover
        estimated_prep_cost_avoided += avoided_prep_units * plan["prep_cost"]

        comparison_data.append({
            "item_name": plan["item_name"],
            "category": plan["category"],
            "suggested_prep": plan["recommended_cook_qty"],
            "prepared": prepared,
            "sold": sold,
            "remaining": current_leftover,
            "sell_through_pct": round((sold / prepared) * 100, 1) if prepared > 0 else 0
        })

    marketplace_revenue = conn.execute("""
        SELECT COALESCE(SUM(total_price), 0)
        FROM marketplace_orders
        WHERE status != 'CANCELLED'
    """).fetchone()[0]

    marketplace_meals = conn.execute("""
        SELECT COALESCE(SUM(quantity), 0)
        FROM marketplace_orders
        WHERE status != 'CANCELLED'
    """).fetchone()[0]

    donated_meals = conn.execute("""
        SELECT COALESCE(SUM(portions), 0)
        FROM ngo_donations
        WHERE status IN ('CLAIMED', 'COLLECTED')
    """).fetchone()[0]

    compost_kg = conn.execute("""
        SELECT COALESCE(SUM(weight_kg), 0)
        FROM composting_logs
    """).fetchone()[0]

    co2_estimate_kg = conn.execute("""
        SELECT COALESCE(SUM(co2_diverted_kg), 0)
        FROM composting_logs
    """).fetchone()[0]

    conn.close()

    portions_avoided = max(0, traditional_waste_portions - current_leftover_portions)
    estimated_waste_avoided_kg = round(portions_avoided * 0.35, 1)
    waste_reduction_pct = (
        round((traditional_waste_portions - current_leftover_portions) / traditional_waste_portions * 100, 1)
        if traditional_waste_portions > 0 else 0
    )

    return render_template(
        "analytics.html",
        settings=settings,
        comparison_data=comparison_data,
        summary={
            "waste_avoided_kg": estimated_waste_avoided_kg,
            "waste_reduction_pct": waste_reduction_pct,
            "avoided_prep_cost": round(estimated_prep_cost_avoided, 2),
            "marketplace_revenue": round(marketplace_revenue, 2),
            "student_meals": marketplace_meals,
            "ngo_meals": donated_meals,
            "total_meals_redistributed": marketplace_meals + donated_meals,
            "compost_kg": round(compost_kg, 1),
            "co2_saved_kg": round(co2_estimate_kg, 1)
        }
    )
