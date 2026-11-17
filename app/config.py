"""
ZeroPlate Configuration Settings
"""

import os
import secrets

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Config:
    # Required by Flask sessions/CSRF. Set SECRET_KEY in the environment for deployment.
    # Fall back to a generated value only for local development so production never
    # relies on an insecure fixed key or missing entropy.
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DATABASE_PATH = os.path.join(BASE_DIR, "data", "zeroplate.db")
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    CANTEEN_NAME = "Graphic Era Central Canteen"
    UNIVERSITY_NAME = "Graphic Era (Deemed to be University), Dehradun"
    STUDENT_NAME = "Yogesh Vyas"
    STUDENT_ROLL = "2106389"
    GUIDE_NAME = "Ms. Shivani Sharma (Assistant Professor)"
