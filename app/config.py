"""
ZeroPlate Configuration Settings
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "zeroplate-dev-key-change-me")
    DATABASE_PATH = os.environ.get(
        "DATABASE_PATH", os.path.join(BASE_DIR, "data", "zeroplate.db")
    )
    DEBUG = False
    CANTEEN_NAME = "Graphic Era Central Canteen"
    UNIVERSITY_NAME = "Graphic Era (Deemed to be University), Dehradun"
    STUDENT_NAME = "Yogesh Vyas"
    STUDENT_ROLL = "2106389"
    GUIDE_NAME = "Ms. Shivani Sharma (Assistant Professor)"
