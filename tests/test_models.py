"""
Unit Tests for ZeroPlate ML Forecasting Models
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from models.predict import get_forecaster

def test_forecaster_initialization():
    forecaster = get_forecaster()
    assert forecaster is not None
    assert forecaster.rf_model is not None
    assert forecaster.gb_model is not None

def test_single_item_prediction():
    forecaster = get_forecaster()
    pred = forecaster.predict_item(
        item_id=101, # Rajma Chawal
        meal_type="Lunch",
        category="Main Course",
        day_of_week=2, # Wednesday
        is_weekend=0,
        is_holiday=0,
        is_exam_day=1,
        temperature_c=24.0,
        rainfall_mm=0.0,
        trend_7d=135.0,
        trend_14d=130.0,
        is_promoted=0
    )

    assert "predicted_demand" in pred
    assert "recommended_cook_qty" in pred
    assert pred["predicted_demand"] > 0
    assert pred["recommended_cook_qty"] >= pred["predicted_demand"]
    assert pred["rf_prediction"] > 0
    assert pred["gb_prediction"] > 0

def test_model_rmse_performance():
    forecaster = get_forecaster()
    metrics = forecaster.get_metrics()
    models = metrics["models"]

    baseline_rmse = models["Baseline (Moving Average)"]["rmse"]
    rf_rmse = models["Random Forest Regressor"]["rmse"]
    gb_rmse = models["Gradient Boosting Regressor"]["rmse"]

    # Both ML models should outperform naive baseline significantly
    assert rf_rmse < baseline_rmse, f"RF RMSE ({rf_rmse}) should be lower than baseline ({baseline_rmse})"
    assert gb_rmse < baseline_rmse, f"GB RMSE ({gb_rmse}) should be lower than baseline ({baseline_rmse})"
    assert gb_rmse < 20.0, f"GB RMSE ({gb_rmse}) exceeds expected threshold"

if __name__ == "__main__":
    test_forecaster_initialization()
    test_single_item_prediction()
    test_model_rmse_performance()
    print("All Model tests passed successfully!")
