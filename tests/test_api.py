"""
Integration Tests for ZeroPlate Web Routes & API Endpoints
"""

import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app

def test_routes():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    # 1. Landing Page
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"ZeroPlate" in resp.data
    assert b"Operations overview" in resp.data
    assert b"Graphic Era" not in resp.data

    # 2. Module 1: Forecast
    resp = client.get("/forecast")
    assert resp.status_code == 200
    assert b"Demand Prediction Dashboard" in resp.data

    # 3. Module 2: Production
    resp = client.get("/production")
    assert resp.status_code == 200
    assert b"Inventory & Production Planning" in resp.data

    # 4. Module 3: Marketplace
    resp = client.get("/marketplace/")
    assert resp.status_code == 200
    assert b"Student Surplus Marketplace" in resp.data

    # 5. Module 4: NGO
    resp = client.get("/ngo/")
    assert resp.status_code == 200
    assert b"NGO Donation Coordination" in resp.data

    # 6. Module 5: Composting
    resp = client.get("/composting/")
    assert resp.status_code == 200
    assert b"Composting & Waste Routing" in resp.data

    # 7. Module 6: Analytics
    resp = client.get("/analytics/")
    assert resp.status_code == 200
    assert b"Analytics & Reporting Dashboard" in resp.data

    # 8. API: Predict
    resp = client.post("/api/predict", 
                       data=json.dumps({"item_id": 101, "day_of_week": 1, "is_exam_day": 1}),
                       content_type="application/json")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["status"] == "success"
    assert "prediction" in data

    # 9. API: Metrics
    resp = client.get("/api/metrics")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["status"] == "success"
    assert "metrics" in data

if __name__ == "__main__":
    test_routes()
    print("All Flask Web & API route tests passed successfully!")
