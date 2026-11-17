"""
ZeroPlate: Surplus Redistribution Escalation Engine
Implements Section 5.3 of the Project Synopsis:

Input: predicted_qty, actual_sold, time_remaining, threshold begin
 remaining_stock = predicted_qty - actual_sold
 if time_remaining < closing_window and remaining_stock > threshold then 
    list item as discounted 'surprise box' on student marketplace 
 end if
 if item unsold at closing_time then
    notify nearest verified NGO with quantity and pickup window 
 end if 
 if item not collected by NGO within pickup window then 
    route item to composting / waste-management channel 
 end if 
end
"""

import random
from datetime import datetime, timedelta
from app.database import get_db_connection

def parse_time_str(time_str):
    """Parses 'HH:MM' string to datetime.time"""
    parts = time_str.split(":")
    return int(parts[0]), int(parts[1])

def minutes_difference(t1_str, t2_str):
    """Returns (t2 - t1) in minutes. Positive if t2 is after t1."""
    h1, m1 = parse_time_str(t1_str)
    h2, m2 = parse_time_str(t2_str)
    return (h2 * 60 + m2) - (h1 * 60 + m1)

def run_escalation_cycle():
    """
    Executes the 3-tier escalation cycle based on current simulated time and stock.
    Returns a dictionary of action logs triggered during the cycle.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get contextual settings
    settings = cursor.execute("SELECT * FROM contextual_settings WHERE id = 1").fetchone()
    if not settings:
        conn.close()
        return {"actions": [], "error": "Contextual settings not initialized"}

    current_time_str = settings["simulated_time"] # e.g. "19:15"
    simulated_date = settings["simulated_date"]
    closing_window_mins = settings["closing_window_mins"] # e.g. 90 mins

    logs = []

    # Fetch daily plans for current simulated date
    daily_plans = cursor.execute("""
        SELECT dp.*, mi.name as item_name, mi.base_price, mi.prep_cost, mi.category
        FROM daily_plans dp
        JOIN menu_items mi ON dp.item_id = mi.id
        WHERE dp.date = ?
    """, (simulated_date,)).fetchall()

    for plan in daily_plans:
        plan_id = plan["id"]
        item_name = plan["item_name"]
        closing_time = plan["closing_time"] # e.g. "20:30"
        threshold = plan["threshold_surplus"] # e.g. 8
        prepared_qty = plan["actual_prepared_qty"]
        sold_qty = plan["actual_sold_qty"]
        
        # Remaining stock calculation
        remaining_stock = prepared_qty - sold_qty
        time_to_close = minutes_difference(current_time_str, closing_time)

        # ---------------------------------------------------------
        # TIER 1: Student Marketplace ('Surprise Box')
        # if time_remaining < closing_window and remaining_stock > threshold
        # ---------------------------------------------------------
        if 0 < time_to_close <= closing_window_mins and remaining_stock > threshold:
            # Check if already listed
            existing_listing = cursor.execute("""
                SELECT * FROM marketplace_items WHERE daily_plan_id = ?
            """, (plan_id,)).fetchone()

            if not existing_listing:
                # 55% discount for student surprise meal box
                orig_price = plan["base_price"]
                disc_price = round(orig_price * 0.45, 0)
                disc_pct = 55
                units_to_list = remaining_stock

                cursor.execute("""
                    INSERT INTO marketplace_items 
                    (daily_plan_id, title, description, original_price, discounted_price, discount_pct, quantity_listed, quantity_claimed, status, listed_at, pickup_until)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'ACTIVE', ?, ?)
                """, (
                    plan_id,
                    f"Surprise {item_name} Box",
                    f"Freshly prepared {item_name}. Help reduce food waste and grab a delicious meal at 55% discount!",
                    orig_price,
                    disc_price,
                    disc_pct,
                    units_to_list,
                    current_time_str,
                    closing_time
                ))
                cursor.execute("""
                    UPDATE daily_plans SET status = 'SURPLUS_DETECTED' WHERE id = ?
                """, (plan_id,))
                conn.commit()
                logs.append(f"[Tier 1 Marketplace] Auto-listed {units_to_list} units of '{item_name}' as Surprise Box at ₹{disc_price} (55% off)")

        # ---------------------------------------------------------
        # TIER 2: NGO Donation Coordination
        # if item unsold at closing_time then notify nearest verified NGO
        # ---------------------------------------------------------
        if time_to_close <= 0:
            # Closing time reached or passed
            # Check if any marketplace listing exists
            mk_item = cursor.execute("""
                SELECT * FROM marketplace_items WHERE daily_plan_id = ?
            """, (plan_id,)).fetchone()

            unsold_after_market = remaining_stock
            if mk_item:
                claimed = mk_item["quantity_claimed"]
                listed = mk_item["quantity_listed"]
                unsold_after_market = max(0, listed - claimed)
                if mk_item["status"] == "ACTIVE":
                    cursor.execute("""
                        UPDATE marketplace_items SET status = 'EXPIRED_TO_NGO' WHERE id = ?
                    """, (mk_item["id"],))
                    conn.commit()

            if unsold_after_market > 0:
                # Check if donation already dispatched for this daily plan
                existing_donation = cursor.execute("""
                    SELECT * FROM ngo_donations WHERE daily_plan_id = ?
                """, (plan_id,)).fetchone()

                if not existing_donation:
                    # Pick verified NGO
                    ngo = cursor.execute("SELECT id, name FROM ngos WHERE verified = 1 LIMIT 1").fetchone()
                    ngo_id = ngo["id"] if ngo else None
                    ngo_name = ngo["name"] if ngo else "Robin Hood Army (Dehradun Chapter)"

                    # Pickup window: 60 minutes after closing
                    ch, cm = parse_time_str(closing_time)
                    deadline_h = (ch + 1) % 24
                    deadline_str = f"{deadline_h:02d}:{cm:02d}"
                    pin = str(random.randint(1000, 9999))

                    cursor.execute("""
                        INSERT INTO ngo_donations 
                        (daily_plan_id, item_name, portions, ngo_id, pickup_window_deadline, status, dispatched_at, verification_pin, notes)
                        VALUES (?, ?, ?, ?, ?, 'PENDING_CLAIM', ?, ?, ?)
                    """, (
                        plan_id,
                        item_name,
                        unsold_after_market,
                        ngo_id,
                        deadline_str,
                        current_time_str,
                        pin,
                        f"Packed in food-grade trays. Temperature checked before packaging."
                    ))
                    cursor.execute("""
                        UPDATE daily_plans SET status = 'CLOSED' WHERE id = ?
                    """, (plan_id,))
                    conn.commit()
                    logs.append(f"[Tier 2 NGO] Escalated {unsold_after_market} unsold portions of '{item_name}' to {ngo_name}. Pickup window until {deadline_str}")

    # ---------------------------------------------------------
    # TIER 3: Composting and Waste Routing
    # if item not collected by NGO within pickup window then route item to composting
    # ---------------------------------------------------------
    pending_donations = cursor.execute("""
        SELECT * FROM ngo_donations WHERE status = 'PENDING_CLAIM'
    """).fetchall()

    for don in pending_donations:
        deadline_str = don["pickup_window_deadline"]
        diff_from_deadline = minutes_difference(current_time_str, deadline_str)
        # If current time is past the deadline by 5+ minutes
        if diff_from_deadline < -5:
            don_id = don["id"]
            portions = don["portions"]
            item_name = don["item_name"]
            weight_kg = round(portions * 0.35, 2) # approx 350g per portion
            compost_kg = round(weight_kg * 0.45, 2)
            co2_diverted = round(weight_kg * 2.5, 2) # kg CO2e saved
            batch_code = f"CMP-{simulated_date.replace('-', '')}-{don_id:03d}"

            cursor.execute("""
                UPDATE ngo_donations SET status = 'EXPIRED_TO_COMPOST' WHERE id = ?
            """, (don_id,))

            cursor.execute("""
                INSERT INTO composting_logs 
                (daily_plan_id, item_name, weight_kg, source_reason, facility_partner, estimated_compost_kg, co2_diverted_kg, logged_at, batch_code)
                VALUES (?, ?, ?, 'EXPIRED_UNCOLLECTED_NGO', 'Main Compost Facility / Green Digester Unit 2', ?, ?, ?, ?)
            """, (
                don["daily_plan_id"],
                item_name,
                weight_kg,
                compost_kg,
                co2_diverted,
                current_time_str,
                batch_code
            ))
            conn.commit()
            logs.append(f"[Tier 3 Composting] NGO pickup window expired for '{item_name}'. Routed {weight_kg}kg ({portions} portions) to Campus Bio-Compost Facility. Batch: {batch_code}")

    conn.close()
    return {"status": "success", "actions": logs}
