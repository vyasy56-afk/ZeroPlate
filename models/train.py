"""
ZeroPlate: Machine Learning Model Training Engine
Trains and evaluates:
1. Random Forest Regressor (RFR)
2. Gradient Boosting Regressor (GBR)
3. Naive Moving Average Baseline for comparison

Computes Root Mean Squared Error (RMSE):
RMSE = sqrt( sum( (p_i - a_i)^2 ) / n )
Also computes MAE, R2 score, and feature importances.
Saves models and metadata for inference in the ZeroPlate platform.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import root_mean_squared_error, mean_absolute_error, r2_score

def train_demand_models():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "canteen_sales_history.csv")
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}. Run data/generate_dataset.py first.")

    print(f"Loading canteen sales dataset from: {data_path}")
    df = pd.read_csv(data_path)

    # Features selected strictly based on Section 5.2 of the ZeroPlate synopsis
    feature_cols = [
        "day_of_week",
        "is_weekend",
        "is_holiday",
        "is_exam_day",
        "temperature_c",
        "rainfall_mm",
        "trend_7d",
        "trend_14d",
        "is_promoted"
    ]

    # Categorical dummy encoding for items and meal categories
    item_dummies = pd.get_dummies(df["item_id"], prefix="item", dtype=float)
    meal_dummies = pd.get_dummies(df["meal_type"], prefix="meal", dtype=float)
    cat_dummies = pd.get_dummies(df["category"], prefix="cat", dtype=float)

    X = pd.concat([df[feature_cols], item_dummies, meal_dummies, cat_dummies], axis=1)
    y = df["actual_demand"].values

    all_features = list(X.columns)

    # Time-series aware 80/20 train/test split (last 20% evaluated as future test window)
    split_idx = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    print(f"Dataset split: {len(X_train)} training records, {len(X_test)} testing records.")

    # 1. Baseline: 7-day rolling average intuition
    y_pred_baseline = df.iloc[split_idx:]["trend_7d"].values
    rmse_baseline = float(root_mean_squared_error(y_test, y_pred_baseline))
    mae_baseline = float(mean_absolute_error(y_test, y_pred_baseline))
    r2_baseline = float(r2_score(y_test, y_pred_baseline))

    # 2. Random Forest Regressor
    print("Training Random Forest Regressor (RFR)...")
    rf_model = RandomForestRegressor(
        n_estimators=120,
        max_depth=12,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)
    y_pred_rf = rf_model.predict(X_test)
    rmse_rf = float(root_mean_squared_error(y_test, y_pred_rf))
    mae_rf = float(mean_absolute_error(y_test, y_pred_rf))
    r2_rf = float(r2_score(y_test, y_pred_rf))

    # 3. Gradient Boosting Regressor
    print("Training Gradient Boosting Regressor (GBR)...")
    gb_model = GradientBoostingRegressor(
        n_estimators=120,
        learning_rate=0.08,
        max_depth=5,
        subsample=0.85,
        random_state=42
    )
    gb_model.fit(X_train, y_train)
    y_pred_gb = gb_model.predict(X_test)
    rmse_gb = float(root_mean_squared_error(y_test, y_pred_gb))
    mae_gb = float(mean_absolute_error(y_test, y_pred_gb))
    r2_gb = float(r2_score(y_test, y_pred_gb))

    # Extract Feature Importances from the best model (GBR/RFR)
    importances = gb_model.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    top_features = []
    for idx in sorted_idx[:12]:
        top_features.append({
            "feature": all_features[idx],
            "importance": round(float(importances[idx]), 4)
        })

    # Summary metrics
    metrics = {
        "formula": "RMSE = sqrt( sum( (p_i - a_i)^2 ) / n )",
        "sample_size_test": len(y_test),
        "models": {
            "Baseline (Moving Average)": {
                "rmse": round(rmse_baseline, 2),
                "mae": round(mae_baseline, 2),
                "r2": round(r2_baseline, 3)
            },
            "Random Forest Regressor": {
                "rmse": round(rmse_rf, 2),
                "mae": round(mae_rf, 2),
                "r2": round(r2_rf, 3)
            },
            "Gradient Boosting Regressor": {
                "rmse": round(rmse_gb, 2),
                "mae": round(mae_gb, 2),
                "r2": round(r2_gb, 3),
                "is_primary": True
            }
        },
        "top_features": top_features,
        "rmse_improvement_vs_baseline_pct": round(float((rmse_baseline - min(rmse_rf, rmse_gb)) / rmse_baseline * 100), 1)
    }

    print("\n==== ZeroPlate Demand Forecasting Evaluation ====")
    print(f"1. Baseline Naive RMSE: {rmse_baseline:.2f} portions (MAE: {mae_baseline:.2f}, R2: {r2_baseline:.3f})")
    print(f"2. Random Forest Regressor RMSE: {rmse_rf:.2f} portions (MAE: {mae_rf:.2f}, R2: {r2_rf:.3f})")
    print(f"3. Gradient Boosting Regressor RMSE: {rmse_gb:.2f} portions (MAE: {mae_gb:.2f}, R2: {r2_gb:.3f})")
    print(f"-> Overfitting/Error Reduction: {metrics['rmse_improvement_vs_baseline_pct']}% error reduction over manual baseline!")

    # Save artifacts
    rf_file = os.path.join(models_dir, "model_rf.pkl")
    gb_file = os.path.join(models_dir, "model_gb.pkl")
    meta_file = os.path.join(models_dir, "feature_meta.json")
    metrics_file = os.path.join(models_dir, "model_metrics.json")

    joblib.dump(rf_model, rf_file)
    joblib.dump(gb_model, gb_file)

    meta = {
        "all_features": all_features,
        "base_feature_cols": feature_cols,
        "item_ids": [int(x) for x in df["item_id"].unique()],
        "meal_types": list(df["meal_type"].unique()),
        "categories": list(df["category"].unique())
    }

    with open(meta_file, "w") as f:
        json.dump(meta, f, indent=2)

    with open(metrics_file, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nModels successfully saved to: {models_dir}")
    return metrics

if __name__ == "__main__":
    train_demand_models()
