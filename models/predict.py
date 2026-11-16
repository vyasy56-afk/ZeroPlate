"""
ZeroPlate: Model Inference and Forecasting Pipeline
Loads trained models (Random Forest / Gradient Boosting) and generates:
- Predicted portion demand
- Uncertainty intervals (standard deviation)
- Safety buffer recommendation for kitchen cooking (prevention before cure)
"""

import os
import json
import joblib
import numpy as np
import pandas as pd

class DemandForecaster:
    def __init__(self, model_type="gb"):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        models_dir = os.path.join(base_dir, "models")
        self.meta_path = os.path.join(models_dir, "feature_meta.json")
        self.metrics_path = os.path.join(models_dir, "model_metrics.json")
        self.rf_path = os.path.join(models_dir, "model_rf.pkl")
        self.gb_path = os.path.join(models_dir, "model_gb.pkl")

        with open(self.meta_path, "r") as f:
            self.meta = json.load(f)

        with open(self.metrics_path, "r") as f:
            self.metrics = json.load(f)

        self.rf_model = joblib.load(self.rf_path)
        self.gb_model = joblib.load(self.gb_path)
        self.model_type = model_type

    def get_metrics(self):
        return self.metrics

    def predict_item(self, item_id, meal_type, category, 
                     day_of_week, is_weekend, is_holiday, is_exam_day,
                     temperature_c, rainfall_mm, trend_7d, trend_14d, is_promoted,
                     safety_buffer_pct=0.08):
        """
        Predicts portion demand for a single item with given context.
        Returns:
            predicted_demand (int)
            recommended_cook_qty (int)
            model_used (str)
            rf_prediction (float)
            gb_prediction (float)
        """
        # Construct feature vector matching one-hot schema
        data = {col: 0.0 for col in self.meta["all_features"]}

        # Base contextual features
        data["day_of_week"] = float(day_of_week)
        data["is_weekend"] = float(is_weekend)
        data["is_holiday"] = float(is_holiday)
        data["is_exam_day"] = float(is_exam_day)
        data["temperature_c"] = float(temperature_c)
        data["rainfall_mm"] = float(rainfall_mm)
        data["trend_7d"] = float(trend_7d)
        data["trend_14d"] = float(trend_14d)
        data["is_promoted"] = float(is_promoted)

        # One-hot encoded keys
        item_col = f"item_{item_id}"
        if item_col in data:
            data[item_col] = 1.0

        meal_col = f"meal_{meal_type}"
        if meal_col in data:
            data[meal_col] = 1.0

        cat_col = f"cat_{category}"
        if cat_col in data:
            data[cat_col] = 1.0

        feature_df = pd.DataFrame([data])[self.meta["all_features"]]

        pred_rf = float(self.rf_model.predict(feature_df)[0])
        pred_gb = float(self.gb_model.predict(feature_df)[0])

        chosen_pred = pred_gb if self.model_type == "gb" else pred_rf
        rounded_pred = max(5, int(round(chosen_pred)))
        # ZeroPlate recommendation adds a modest, data-informed safety buffer (e.g. 5-8% vs traditional 25%)
        recommended_cook_qty = int(round(rounded_pred * (1 + safety_buffer_pct)))

        return {
            "predicted_demand": rounded_pred,
            "recommended_cook_qty": recommended_cook_qty,
            "rf_prediction": round(pred_rf, 1),
            "gb_prediction": round(pred_gb, 1),
            "safety_buffer_units": recommended_cook_qty - rounded_pred,
            "model_used": "Gradient Boosting Regressor" if self.model_type == "gb" else "Random Forest Regressor"
        }

    def predict_daily_menu(self, context_dict, items_list):
        """
        Runs batch predictions for all items on a day's menu.
        """
        results = []
        for item in items_list:
            pred = self.predict_item(
                item_id=item["item_id"],
                meal_type=item["meal_type"],
                category=item["category"],
                day_of_week=context_dict["day_of_week"],
                is_weekend=context_dict.get("is_weekend", 1 if context_dict["day_of_week"] in [5, 6] else 0),
                is_holiday=context_dict.get("is_holiday", 0),
                is_exam_day=context_dict.get("is_exam_day", 0),
                temperature_c=context_dict.get("temperature_c", 24.0),
                rainfall_mm=context_dict.get("rainfall_mm", 0.0),
                trend_7d=item.get("trend_7d", item.get("base_demand", 100)),
                trend_14d=item.get("trend_14d", item.get("base_demand", 100)),
                is_promoted=item.get("is_promoted", 0),
                safety_buffer_pct=context_dict.get("safety_buffer_pct", 0.08)
            )
            item_result = dict(item)
            item_result.update(pred)
            results.append(item_result)
        return results

# Singleton instance helper
_forecaster_instance = None

def get_forecaster():
    global _forecaster_instance
    if _forecaster_instance is None:
        _forecaster_instance = DemandForecaster()
    return _forecaster_instance
