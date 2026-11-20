"""
ZeroPlate: Application Factory
Food demand planning and surplus recovery application
"""

import os
import sys
from flask import Flask

# Ensure project root is in python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.config import Config
from app.database import init_db


def _seed_demo_data_when_requested(app):
    """Populate a fresh demo database when explicitly enabled (e.g. Vercel demo).

    Vercel's /tmp filesystem is ephemeral and instance-local. This restores a
    useful demo dataset whenever a fresh serverless instance starts; it does
    not provide cross-instance or durable persistence for owner edits.
    """
    if os.environ.get("ZERO_PLATE_AUTO_SEED_DEMO") != "1":
        return

    from app.database import get_db_connection

    conn = get_db_connection()
    try:
        settings = conn.execute(
            "SELECT simulated_date FROM contextual_settings WHERE id = 1"
        ).fetchone()
        if not settings:
            app.logger.warning("Demo seed skipped: operating date is not configured.")
            return

        demo_date = settings["simulated_date"]
        existing = conn.execute(
            "SELECT COUNT(*) AS total FROM daily_plans WHERE date = ?",
            (demo_date,),
        ).fetchone()["total"]
    finally:
        conn.close()

    if existing:
        app.logger.info(
            "Demo seed skipped: %s plan(s) already exist for %s.",
            existing,
            demo_date,
        )
        return

    try:
        from app.seed_demo import seed_operational_day

        seeded = seed_operational_day(sim_date=demo_date)
        if seeded:
            app.logger.info("ZeroPlate demo data seeded for %s.", demo_date)
    except Exception:
        # Keep the application available even if optional demo seeding fails.
        app.logger.exception("ZeroPlate demo data could not be seeded.")


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize the operational database on startup.
    with app.app_context():
        init_db()
        _seed_demo_data_when_requested(app)

    # Register blueprints
    from app.routes.dashboard import dashboard_bp
    from app.routes.marketplace import marketplace_bp
    from app.routes.ngo import ngo_bp
    from app.routes.composting import composting_bp
    from app.routes.analytics import analytics_bp
    from app.routes.api import api_bp
    from app.routes.owner import owner_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(marketplace_bp)
    app.register_blueprint(ngo_bp)
    app.register_blueprint(composting_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(owner_bp)

    @app.context_processor
    def inject_global_vars():
        return {
            "app_name": "ZeroPlate",
            "tagline": "Food demand planning and surplus recovery"
        }

    return app
