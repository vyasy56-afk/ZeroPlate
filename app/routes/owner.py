"""
Owner-only menu management.

The owner password is configured with the OWNER_PASSWORD environment variable.
No owner password is hard-coded into the repository.
"""

import secrets
from datetime import datetime
from functools import wraps

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.database import get_db_connection
from models.predict import get_forecaster

owner_bp = Blueprint("owner", __name__, url_prefix="/owner")

MEAL_TYPES = ("Breakfast", "Lunch", "Snacks", "Dinner")


def owner_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("owner_authenticated"):
            return redirect(url_for("owner.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def _read_dish_form(form):
    name = (form.get("name") or "").strip()
    category = (form.get("category") or "").strip()
    meal_type = (form.get("meal_type") or "").strip()
    emoji = (form.get("image_emoji") or "🍲").strip() or "🍲"

    if not name or len(name) > 80:
        raise ValueError("Enter a dish name between 1 and 80 characters.")
    if not category or len(category) > 60:
        raise ValueError("Enter a category between 1 and 60 characters.")
    if meal_type not in MEAL_TYPES:
        raise ValueError("Choose a valid meal type.")
    if len(emoji) > 8:
        raise ValueError("Use a short food icon.")

    try:
        price = float(form.get("base_price", ""))
        prep_cost = float(form.get("prep_cost", ""))
        shelf_life = int(form.get("shelf_life_hours", "6"))
        base_demand = int(form.get("base_demand", "100"))
    except (TypeError, ValueError):
        raise ValueError("Enter valid numbers for price, cost, shelf life and expected daily servings.")

    if not (0.01 <= price <= 100000):
        raise ValueError("Selling price must be greater than ₹0 and no more than ₹100,000.")
    if not (0 <= prep_cost <= 100000):
        raise ValueError("Preparation cost must be between ₹0 and ₹100,000.")
    if not (1 <= shelf_life <= 72):
        raise ValueError("Shelf life must be between 1 and 72 hours.")
    if not (1 <= base_demand <= 10000):
        raise ValueError("Recent average servings must be between 1 and 10,000.")

    return {
        "name": name,
        "category": category,
        "meal_type": meal_type,
        "base_price": round(price, 2),
        "prep_cost": round(prep_cost, 2),
        "shelf_life_hours": shelf_life,
        "image_emoji": emoji,
        "base_demand": base_demand,
    }


@owner_bp.route("/")
def home():
    if session.get("owner_authenticated"):
        return redirect(url_for("owner.menu"))
    return redirect(url_for("owner.login"))


@owner_bp.route("/login", methods=["GET", "POST"])
def login():
    configured_password = current_app.config.get("OWNER_PASSWORD", "")
    error = ""

    if request.method == "POST":
        supplied_password = request.form.get("password", "")
        if not configured_password:
            error = "Owner access is not configured yet. Set OWNER_PASSWORD and restart the application."
        elif secrets.compare_digest(supplied_password, configured_password):
            session.clear()
            session["owner_authenticated"] = True
            return redirect(url_for("owner.menu"))
        else:
            error = "The owner password is incorrect."

    return render_template(
        "owner_login.html",
        password_configured=bool(configured_password),
        error=error,
    )


@owner_bp.route("/logout", methods=["POST"])
@owner_required
def logout():
    session.clear()
    return redirect(url_for("owner.login"))


@owner_bp.route("/menu")
@owner_required
def menu():
    conn = get_db_connection()
    settings = conn.execute(
        "SELECT simulated_date FROM contextual_settings WHERE id = 1"
    ).fetchone()
    today = settings["simulated_date"] if settings else datetime.now().strftime("%Y-%m-%d")

    items = conn.execute("""
        SELECT *
        FROM menu_items
        ORDER BY is_active DESC, category, name
    """).fetchall()

    planned_ids = {
        row["item_id"]
        for row in conn.execute(
            "SELECT item_id FROM daily_plans WHERE date = ?",
            (today,),
        ).fetchall()
    }
    conn.close()

    active_count = sum(1 for item in items if item["is_active"])
    return render_template(
        "owner_menu.html",
        menu_items=items,
        planned_ids=planned_ids,
        today=today,
        active_count=active_count,
        notice=request.args.get("notice", ""),
        error=request.args.get("error", ""),
    )


@owner_bp.route("/menu/add", methods=["POST"])
@owner_required
def add_dish():
    try:
        dish = _read_dish_form(request.form)
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO menu_items
            (name, category, meal_type, base_price, prep_cost, shelf_life_hours,
             image_emoji, base_demand, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            dish["name"], dish["category"], dish["meal_type"],
            dish["base_price"], dish["prep_cost"], dish["shelf_life_hours"],
            dish["image_emoji"], dish["base_demand"],
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("owner.menu", notice="added"))
    except ValueError as exc:
        return redirect(url_for("owner.menu", error=str(exc)))


@owner_bp.route("/menu/<int:item_id>/update", methods=["POST"])
@owner_required
def update_dish(item_id):
    try:
        dish = _read_dish_form(request.form)
        conn = get_db_connection()
        cursor = conn.execute("""
            UPDATE menu_items
            SET name = ?, category = ?, meal_type = ?, base_price = ?,
                prep_cost = ?, shelf_life_hours = ?, image_emoji = ?,
                base_demand = ?
            WHERE id = ?
        """, (
            dish["name"], dish["category"], dish["meal_type"],
            dish["base_price"], dish["prep_cost"], dish["shelf_life_hours"],
            dish["image_emoji"], dish["base_demand"], item_id,
        ))
        conn.commit()
        changed = cursor.rowcount
        conn.close()
        if not changed:
            return redirect(url_for("owner.menu", error="Dish not found."))
        return redirect(url_for("owner.menu", notice="updated"))
    except ValueError as exc:
        return redirect(url_for("owner.menu", error=str(exc)))


@owner_bp.route("/menu/<int:item_id>/toggle", methods=["POST"])
@owner_required
def toggle_dish(item_id):
    conn = get_db_connection()
    item = conn.execute(
        "SELECT id, is_active FROM menu_items WHERE id = ?",
        (item_id,),
    ).fetchone()
    if not item:
        conn.close()
        return redirect(url_for("owner.menu", error="Dish not found."))

    new_value = 0 if item["is_active"] else 1
    conn.execute(
        "UPDATE menu_items SET is_active = ? WHERE id = ?",
        (new_value, item_id),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("owner.menu", notice="activated" if new_value else "deactivated"))


@owner_bp.route("/menu/<int:item_id>/plan", methods=["POST"])
@owner_required
def add_to_today_plan(item_id):
    conn = get_db_connection()
    item = conn.execute(
        "SELECT * FROM menu_items WHERE id = ? AND is_active = 1",
        (item_id,),
    ).fetchone()
    settings = conn.execute(
        "SELECT * FROM contextual_settings WHERE id = 1"
    ).fetchone()

    if not item or not settings:
        conn.close()
        return redirect(url_for("owner.menu", error="Dish or operating settings were not found."))

    existing = conn.execute(
        "SELECT id FROM daily_plans WHERE date = ? AND item_id = ?",
        (settings["simulated_date"], item_id),
    ).fetchone()
    if existing:
        conn.close()
        return redirect(url_for("owner.menu", notice="already-planned"))

    try:
        day_of_week = int(settings["day_of_week"])
        prediction = get_forecaster().predict_item(
            item_id=item["id"],
            meal_type=item["meal_type"],
            category=item["category"],
            day_of_week=day_of_week,
            is_weekend=1 if day_of_week in (5, 6) else 0,
            is_holiday=int(settings["is_holiday"]),
            is_exam_day=0,
            temperature_c=float(settings["temperature_c"]),
            rainfall_mm=float(settings["rainfall_mm"]),
            trend_7d=float(item["base_demand"]),
            trend_14d=float(item["base_demand"]),
            is_promoted=0,
            safety_buffer_pct=0.08,
        )
        closing_times = {
            "Breakfast": "11:00",
            "Lunch": "15:30",
            "Snacks": "18:30",
            "Dinner": "21:00",
        }
        conn.execute("""
            INSERT INTO daily_plans
            (date, item_id, predicted_demand, recommended_cook_qty,
             actual_prepared_qty, actual_sold_qty, status, safety_buffer,
             threshold_surplus, closing_time)
            VALUES (?, ?, ?, ?, 0, 0, 'PLANNED', ?, 8, ?)
        """, (
            settings["simulated_date"],
            item_id,
            prediction["predicted_demand"],
            prediction["recommended_cook_qty"],
            prediction["safety_buffer_units"],
            closing_times.get(item["meal_type"], "20:30"),
        ))
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        current_app.logger.exception("Could not add dish to today's menu plan")
        return redirect(url_for("owner.menu", error="The demand estimate could not be created. Please try again."))
    conn.close()
    return redirect(url_for("owner.menu", notice="planned"))
