"""
ZeroPlate: Application Factory
Project: ZeroPlate - AI-Powered Food Demand Forecasting and Surplus Redistribution
Author: Yogesh Vyas · BCA (AI & DS) · Graphic Era (Deemed to be University)
Guide: Ms. Shivani Sharma (Assistant Professor)
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

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize SQLite database on startup
    with app.app_context():
        init_db()

    # Register blueprints
    from app.routes.dashboard import dashboard_bp
    from app.routes.marketplace import marketplace_bp
    from app.routes.ngo import ngo_bp
    from app.routes.composting import composting_bp
    from app.routes.analytics import analytics_bp
    from app.routes.api import api_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(marketplace_bp)
    app.register_blueprint(ngo_bp)
    app.register_blueprint(composting_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(api_bp)

    @app.context_processor
    def inject_global_vars():
        return {
            "app_name": "ZeroPlate",
            "tagline": "AI-Powered Demand Forecasting & Surplus Redistribution",
            "author_name": "Yogesh Vyas",
            "roll_no": "2106389",
            "department": "BCA (AI & DS)",
            "institution": "Graphic Era (Deemed to be University), Dehradun",
            "guide_name": "Ms. Shivani Sharma (Assistant Professor)"
        }

    return app
