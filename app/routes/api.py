"""
ZeroPlate: REST API Endpoints
Handles AJAX / API requests for:
- Demand forecasting inference
- Marketplace claims
- NGO coordination and PIN verification
- Composting logging
- Simulation state adjustments and instant escalation cycle triggers
"""

import random
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.database import get_db_connection
from models.predict import get_forecaster
from app.escalation_engine import run_escalation_cycle

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/predict", methods=["POST"])
def predict():
    """
    On-demand prediction endpoint for any item with arbitrary contextual parameters.
    """
    data = request.get_json() or {}
    item_id = int(data.get("item_id", 101))
    day_of_week = int(data.get("day_of_week", 0))
    is_weekend = int(data.get("is_weekend", 1 if day_of_week in [5, 6] else 0))
    is_holiday = int(data.get("is_holiday", 0))
    is_exam_day = int(data.get("is_exam_day", 0))
    temperature_c = float(data.get("temperature_c", 24.0))
    rainfall_mm = float(data.get("rainfall_mm", 0.0))
    trend_7d = float(data.get("trend_7d", 120.0))
    trend_14d = float(data.get("trend_14d", 120.0))
    is_promoted = int(data.get("is_promoted", 0))

    conn = get_db_connection()
    item = conn.execute("SELECT * FROM menu_items WHERE id = ?", (item_id,)).fetchone()
    conn.close()

    if not item:
        return jsonify({"error": f"Item id {item_id} not found"}), 404

    forecaster = get_forecaster()
    result = forecaster.predict_item(
        item_id=item_id,
        meal_type=item["meal_type"],
        category=item["category"],
        day_of_week=day_of_week,
        is_weekend=is_weekend,
        is_holiday=is_holiday,
        is_exam_day=is_exam_day,
        temperature_c=temperature_c,
        rainfall_mm=rainfall_mm,
        trend_7d=trend_7d,
        trend_14d=trend_14d,
        is_promoted=is_promoted
    )

    result["item_name"] = item["name"]
    result["category"] = item["category"]
    result["meal_type"] = item["meal_type"]
    result["base_price"] = item["base_price"]

    return jsonify({"status": "success", "prediction": result})

@api_bp.route("/marketplace/claim", methods=["POST"])
def claim_marketplace_item():
    """
    Handles student reservation of a discounted surprise box.
    """
    data = request.get_json() or {}
    listing_id = data.get("listing_id")
    student_name = data.get("student_name", "Student").strip()
    student_roll = data.get("student_roll", "STU-001").strip()
    qty = int(data.get("quantity", 1))

    if not listing_id or not student_name or not student_roll:
        return jsonify({"error": "Missing listing ID or student details"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    item = cursor.execute("SELECT * FROM marketplace_items WHERE id = ?", (listing_id,)).fetchone()
    if not item:
        conn.close()
        return jsonify({"error": "Listing not found"}), 404

    available = item["quantity_listed"] - item["quantity_claimed"]
    if qty > available:
        conn.close()
        return jsonify({"error": f"Only {available} units available"}), 400

    token = f"ZP-TK-{random.randint(1000, 9999)}"
    total_price = item["discounted_price"] * qty

    cursor.execute("""
        INSERT INTO marketplace_orders 
        (marketplace_item_id, student_name, student_id_roll, quantity, total_price, token_code, status, ordered_at)
        VALUES (?, ?, ?, ?, ?, ?, 'RESERVED', ?)
    """, (listing_id, student_name, student_roll, qty, total_price, token, datetime.now().strftime("%H:%M")))

    new_claimed = item["quantity_claimed"] + qty
    new_status = "SOLD_OUT" if new_claimed >= item["quantity_listed"] else "ACTIVE"

    cursor.execute("""
        UPDATE marketplace_items SET quantity_claimed = ?, status = ? WHERE id = ?
    """, (new_claimed, new_status, listing_id))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": f"Successfully reserved {qty}x {item['title']}!",
        "token": token,
        "total_price": total_price,
        "pickup_until": item["pickup_until"]
    })

@api_bp.route("/ngo/claim", methods=["POST"])
def claim_ngo_donation():
    """
    NGO claims a pending food donation batch.
    """
    data = request.get_json() or {}
    donation_id = data.get("donation_id")
    ngo_id = data.get("ngo_id", 1)
    volunteer_name = data.get("volunteer_name", "Assigned Volunteer")

    conn = get_db_connection()
    cursor = conn.cursor()

    donation = cursor.execute("SELECT * FROM ngo_donations WHERE id = ?", (donation_id,)).fetchone()
    if not donation:
        conn.close()
        return jsonify({"error": "Donation record not found"}), 404

    if donation["status"] != "PENDING_CLAIM":
        conn.close()
        return jsonify({"error": f"Donation is already {donation['status']}"}), 400

    now_str = datetime.now().strftime("%H:%M")
    cursor.execute("""
        UPDATE ngo_donations SET 
            status = 'CLAIMED',
            ngo_id = ?,
            claimed_at = ?,
            notes = notes || ' [Claimed by ' || ? || ']'
        WHERE id = ?
    """, (ngo_id, now_str, volunteer_name, donation_id))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": f"Donation claimed successfully! Please verify pickup with PIN before deadline."
    })

@api_bp.route("/ngo/verify-pickup", methods=["POST"])
def verify_ngo_pickup():
    """
    Verifies pickup of food donation by matching canteen's 4-digit PIN.
    """
    data = request.get_json() or {}
    donation_id = data.get("donation_id")
    entered_pin = str(data.get("pin", "")).strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    donation = cursor.execute("SELECT * FROM ngo_donations WHERE id = ?", (donation_id,)).fetchone()
    if not donation:
        conn.close()
        return jsonify({"error": "Donation record not found"}), 404

    if donation["verification_pin"] != entered_pin:
        conn.close()
        return jsonify({"error": "Invalid verification PIN. Please confirm with canteen staff."}), 400

    now_str = datetime.now().strftime("%H:%M")
    cursor.execute("""
        UPDATE ngo_donations SET 
            status = 'COLLECTED',
            collected_at = ?
        WHERE id = ?
    """, (now_str, donation_id))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": f"Handover verified! {donation['portions']} portions of {donation['item_name']} collected safely."
    })

@api_bp.route("/production/update-status", methods=["POST"])
def update_production_status():
    """
    Updates kitchen production progress (PLANNED -> COOKING -> IN_SERVICE -> CLOSED)
    """
    data = request.get_json() or {}
    plan_id = data.get("plan_id")
    new_status = data.get("status")
    actual_prepared = data.get("actual_prepared_qty")

    if not plan_id or not new_status:
        return jsonify({"error": "Missing plan_id or status"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    if actual_prepared is not None:
        cursor.execute("UPDATE daily_plans SET status = ?, actual_prepared_qty = ? WHERE id = ?", (new_status, int(actual_prepared), plan_id))
    else:
        cursor.execute("UPDATE daily_plans SET status = ? WHERE id = ?", (new_status, plan_id))

    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": f"Plan #{plan_id} updated to {new_status}"})

@api_bp.route("/simulation/update-state", methods=["POST"])
def update_simulation_state():
    """
    Allows user to test and demonstrate the 3-tier escalation cycle by modifying:
    - simulated_time (e.g., advance to closing time or past pickup window)
    - simulated_date
    - weather conditions
    - exam day / holiday status
    Automatically triggers run_escalation_cycle()!
    """
    data = request.get_json() or {}
    sim_time = data.get("simulated_time", "19:45")
    sim_date = data.get("simulated_date")
    is_exam = int(data.get("is_exam_day", 0))
    is_holiday = int(data.get("is_holiday", 0))
    temp = float(data.get("temperature_c", 23.5))
    rain = float(data.get("rainfall_mm", 0.0))
    closing_window = int(data.get("closing_window_mins", 90))

    conn = get_db_connection()
    cursor = conn.cursor()

    if sim_date:
        cursor.execute("""
            UPDATE contextual_settings SET
                simulated_time = ?,
                simulated_date = ?,
                is_exam_day = ?,
                is_holiday = ?,
                temperature_c = ?,
                rainfall_mm = ?,
                closing_window_mins = ?
            WHERE id = 1
        """, (sim_time, sim_date, is_exam, is_holiday, temp, rain, closing_window))
    else:
        cursor.execute("""
            UPDATE contextual_settings SET
                simulated_time = ?,
                is_exam_day = ?,
                is_holiday = ?,
                temperature_c = ?,
                rainfall_mm = ?,
                closing_window_mins = ?
            WHERE id = 1
        """, (sim_time, is_exam, is_holiday, temp, rain, closing_window))

    conn.commit()
    conn.close()

    # Trigger escalation engine immediately
    escalation_result = run_escalation_cycle()

    return jsonify({
        "status": "success",
        "message": f"Simulation clock advanced to {sim_time}.",
        "escalation_actions": escalation_result.get("actions", [])
    })

@api_bp.route("/metrics", methods=["GET"])
def get_metrics():
    """
    Returns aggregated live platform metrics.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Calculate avoidance & recovery metrics
    plans = cursor.execute("""
        SELECT dp.*, mi.base_price, mi.prep_cost 
        FROM daily_plans dp 
        JOIN menu_items mi ON dp.item_id = mi.id
    """).fetchall()

    traditional_waste_portions = 0
    zeroplate_waste_portions = 0
    cost_saved = 0.0

    for p in plans:
        # Traditional overproduction was base * 1.25
        trad_prep = int(round(p["predicted_demand"] * 1.25))
        sold = p["actual_sold_qty"]
        trad_waste = max(0, trad_prep - sold)
        actual_waste = max(0, p["actual_prepared_qty"] - sold)

        traditional_waste_portions += trad_waste
        zeroplate_waste_portions += actual_waste
        # Avoided prep cost
        avoided_units = max(0, trad_prep - p["actual_prepared_qty"])
        cost_saved += (avoided_units * p["prep_cost"])

    # Marketplace revenue recovered
    marketplace_rev = cursor.execute("""
        SELECT COALESCE(SUM(total_price), 0) FROM marketplace_orders WHERE status != 'CANCELLED'
    """).fetchone()[0]

    # Meals saved via student marketplace
    marketplace_meals = cursor.execute("""
        SELECT COALESCE(SUM(quantity), 0) FROM marketplace_orders WHERE status != 'CANCELLED'
    """).fetchone()[0]

    # Meals donated to NGO
    ngo_meals = cursor.execute("""
        SELECT COALESCE(SUM(portions), 0) FROM ngo_donations WHERE status IN ('CLAIMED', 'COLLECTED')
    """).fetchone()[0]

    # Organic compost diverted
    compost_kg = cursor.execute("""
        SELECT COALESCE(SUM(weight_kg), 0) FROM composting_logs
    """).fetchone()[0]

    co2_diverted_kg = cursor.execute("""
        SELECT COALESCE(SUM(co2_diverted_kg), 0) FROM composting_logs
    """).fetchone()[0]

    conn.close()

    portions_avoided = max(0, traditional_waste_portions - zeroplate_waste_portions)
    total_food_waste_avoided_kg = round(portions_avoided * 0.35, 1)
    waste_reduction_pct = (
        round((traditional_waste_portions - zeroplate_waste_portions) / traditional_waste_portions * 100, 1)
        if traditional_waste_portions > 0 else 0
    )
    total_savings_inr = round(cost_saved + marketplace_rev, 2)

    return jsonify({
        "status": "success",
        "metrics": {
            "projected_waste_avoided_kg": total_food_waste_avoided_kg,
            "waste_reduction_pct": waste_reduction_pct,
            "cost_saved_inr": total_savings_inr,
            "marketplace_revenue_recovered": round(marketplace_rev, 2),
            "student_meals_redistributed": marketplace_meals,
            "ngo_meals_donated": ngo_meals,
            "compost_diverted_kg": round(compost_kg, 1),
            "co2_emissions_saved_kg": round(co2_diverted_kg, 1)
        }
    })
