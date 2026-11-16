"""
ZeroPlate: NGO Donation Coordination Routes
Module 4: NGO Donation Coordination
Escalates unsold food at closing time to verified partner NGOs.
Provides pickup window countdown, dispatch claiming, and secure PIN handover.
"""

from flask import Blueprint, render_template
from app.database import get_db_connection

ngo_bp = Blueprint("ngo", __name__, url_prefix="/ngo")

@ngo_bp.route("/")
def index():
    conn = get_db_connection()
    settings = conn.execute("SELECT * FROM contextual_settings WHERE id = 1").fetchone()

    # Active and pending donations
    donations = conn.execute("""
        SELECT nd.*, n.name as ngo_name, n.phone as ngo_phone, n.contact_person
        FROM ngo_donations nd
        LEFT JOIN ngos n ON nd.ngo_id = n.id
        ORDER BY 
            CASE nd.status 
                WHEN 'PENDING_CLAIM' THEN 1 
                WHEN 'CLAIMED' THEN 2 
                WHEN 'COLLECTED' THEN 3 
                ELSE 4 
            END,
            nd.id DESC
    """).fetchall()

    # List verified NGOs
    ngos = conn.execute("SELECT * FROM ngos WHERE verified = 1").fetchall()

    conn.close()

    return render_template("ngo.html", 
                           settings=settings, 
                           donations=donations, 
                           ngos=ngos)
