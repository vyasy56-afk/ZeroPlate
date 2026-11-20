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
