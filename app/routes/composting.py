"""
ZeroPlate: Composting and Waste Routing Routes
Module 5: Composting/Waste-Channel Routing
Ensures that if donation pickup is not completed in the safe window,
unavoidable surplus is diverted to organic composting rather than landfills.
"""

from flask import Blueprint, render_template
from app.database import get_db_connection

composting_bp = Blueprint("composting", __name__, url_prefix="/composting")

@composting_bp.route("/")
def index():
    conn = get_db_connection()
    settings = conn.execute("SELECT * FROM contextual_settings WHERE id = 1").fetchone()

    logs = conn.execute("""
        SELECT * FROM composting_logs
        ORDER BY id DESC
    """).fetchall()

    total_weight = sum(l["weight_kg"] for l in logs)
    total_compost = sum(l["estimated_compost_kg"] for l in logs)
    total_co2 = sum(l["co2_diverted_kg"] for l in logs)

    conn.close()

    return render_template("composting.html", 
                           settings=settings, 
                           logs=logs,
                           totals={
                               "weight_kg": round(total_weight, 1),
                               "compost_kg": round(total_compost, 1),
                               "co2_diverted_kg": round(total_co2, 1)
                           })
