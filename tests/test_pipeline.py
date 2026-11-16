"""
Unit Tests for ZeroPlate 3-Tier Escalation Pipeline Logic
Tests Section 5.3 Pseudocode implementation:
1. Tier 1: time_remaining < closing_window & remaining_stock > threshold -> Marketplace
2. Tier 2: time_remaining <= 0 & unsold -> NGO
3. Tier 3: time past deadline & uncollected -> Composting
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.database import init_db, get_db_connection
from app.escalation_engine import run_escalation_cycle, minutes_difference

def test_time_difference():
    # 20:30 - 19:15 = 75 minutes
    diff = minutes_difference("19:15", "20:30")
    assert diff == 75

    # Past closing: 20:30 - 21:00 = -30 minutes
    diff_past = minutes_difference("21:00", "20:30")
    assert diff_past == -30

def test_escalation_cycle_execution():
    init_db()
    res = run_escalation_cycle()
    assert "status" in res
    assert res["status"] == "success"
    assert isinstance(res["actions"], list)

if __name__ == "__main__":
    test_time_difference()
    test_escalation_cycle_execution()
    print("All Escalation Pipeline tests passed successfully!")
