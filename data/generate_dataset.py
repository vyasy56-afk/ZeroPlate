"""
ZeroPlate: Data Generator
Generates realistic historical canteen sales data with contextual variables:
- Day of week, weekend indicator
- Public holidays and university exam periods (Graphic Era academic schedule)
- Weather data (Temperature in Celsius, Rainfall in mm)
- 7-day and 14-day rolling sales trends
- Item promotions and menu variations
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Seed for reproducibility
np.random.seed(42)
random.seed(42)

# Menu Catalog for Graphic Era University Canteen & Food Service
MENU_ITEMS = [
    {
        "item_id": 101,
        "item_name": "Rajma Chawal",
        "category": "Main Course",
        "meal_type": "Lunch",
        "base_demand": 140,
        "base_price": 80.0,
        "prep_cost": 35.0,
        "shelf_life_hours": 6,
        "weather_sensitivity": "rain_boost" # People love warm comfort food on rainy days
    },
    {
        "item_id": 102,
        "item_name": "Paneer Butter Masala Thali",
        "category": "Thali",
        "meal_type": "Lunch",
        "base_demand": 110,
        "base_price": 130.0,
        "prep_cost": 55.0,
        "shelf_life_hours": 5,
        "weather_sensitivity": "neutral"
    },
    {
        "item_id": 103,
        "item_name": "Dal Makhani & Naan Combo",
        "category": "Main Course",
        "meal_type": "Dinner",
        "base_demand": 95,
        "base_price": 110.0,
        "prep_cost": 48.0,
        "shelf_life_hours": 6,
        "weather_sensitivity": "cold_boost"
    },
    {
        "item_id": 104,
        "item_name": "Veg Dum Biryani",
        "category": "Rice Specialties",
        "meal_type": "Lunch",
        "base_demand": 125,
        "base_price": 120.0,
        "prep_cost": 50.0,
        "shelf_life_hours": 5,
        "weather_sensitivity": "weekend_boost"
    },
    {
        "item_id": 105,
        "item_name": "Chole Bhature",
        "category": "North Indian",
        "meal_type": "Breakfast",
        "base_demand": 115,
        "base_price": 70.0,
        "prep_cost": 30.0,
        "shelf_life_hours": 4,
        "weather_sensitivity": "rain_boost"
    },
    {
        "item_id": 106,
        "item_name": "Masala Dosa with Sambar",
        "category": "South Indian",
        "meal_type": "Breakfast",
        "base_demand": 90,
        "base_price": 65.0,
        "prep_cost": 26.0,
        "shelf_life_hours": 4,
        "weather_sensitivity": "neutral"
    },
    {
        "item_id": 107,
        "item_name": "Crispy Samosa Plate (2 pcs)",
        "category": "Quick Bites",
        "meal_type": "Snacks",
        "base_demand": 180,
        "base_price": 30.0,
        "prep_cost": 12.0,
        "shelf_life_hours": 8,
        "weather_sensitivity": "rain_boost" # Huge jump on rainy days and exam days
    },
    {
        "item_id": 108,
        "item_name": "Aloo Paratha with Curd & Pickle",
        "category": "Breakfast",
        "meal_type": "Breakfast",
        "base_demand": 85,
        "base_price": 50.0,
        "prep_cost": 20.0,
        "shelf_life_hours": 4,
        "weather_sensitivity": "cold_boost"
    },
    {
        "item_id": 109,
        "item_name": "Cold Coffee Shake",
        "category": "Beverages",
        "meal_type": "Snacks",
        "base_demand": 130,
        "base_price": 45.0,
        "prep_cost": 18.0,
        "shelf_life_hours": 12,
        "weather_sensitivity": "hot_boost" # Surges during hot days & exam study sessions
    },
    {
        "item_id": 110,
        "item_name": "Gulab Jamun (2 pcs)",
        "category": "Desserts",
        "meal_type": "Dinner",
        "base_demand": 75,
        "base_price": 40.0,
        "prep_cost": 15.0,
        "shelf_life_hours": 24,
        "weather_sensitivity": "festival_boost"
    }
]

def generate_contextual_dataset(start_date="2026-03-01", days=240):
    """
    Simulates daily canteen demand over several months, accounting for:
    - Academic calendar (exams, vacation, normal semesters)
    - Dehradun weather patterns (spring, hot summer, monsoon, autumn)
    - Weekly patterns (weekday vs weekend)
    - Public holidays
    - Menu promotions
    """
    records = []
    base_dt = datetime.strptime(start_date, "%Y-%m-%d")

    # Keep track of recent item demand for 7d and 14d rolling trend computation
    history_tracker = {item["item_id"]: [] for item in MENU_ITEMS}

    for day_idx in range(days):
        current_date = base_dt + timedelta(days=day_idx)
        date_str = current_date.strftime("%Y-%m-%d")
        day_of_week = current_date.weekday() # 0 = Monday, 6 = Sunday
        is_weekend = 1 if day_of_week in [5, 6] else 0

        # Month-dependent Dehradun weather simulation
        month = current_date.month
        if month in [12, 1, 2]: # Winter
            avg_temp = 15.0 + np.random.normal(0, 3.0)
            rainfall = max(0.0, np.random.exponential(1.5) if random.random() < 0.2 else 0.0)
        elif month in [3, 4, 5]: # Spring / Hot Summer
            avg_temp = 28.0 + np.random.normal(0, 4.0)
            rainfall = max(0.0, np.random.exponential(3.0) if random.random() < 0.15 else 0.0)
        elif month in [6, 7, 8, 9]: # Monsoon
            avg_temp = 27.0 + np.random.normal(0, 2.5)
            # 65% chance of rain in monsoon
            rainfall = max(0.0, np.random.gamma(shape=2.5, scale=8.0) if random.random() < 0.65 else 0.0)
        else: # Autumn (Oct, Nov)
            avg_temp = 22.0 + np.random.normal(0, 3.0)
            rainfall = max(0.0, np.random.exponential(2.0) if random.random() < 0.1 else 0.0)
        
        temperature = round(float(np.clip(avg_temp, 8.0, 42.0)), 1)
        rainfall = round(float(rainfall), 1)

        # Academic Calendar & Holidays Simulation
        # Mid-terms in April, Finals in June/July, Mid-terms in October, Finals in Dec
        is_exam_day = 0
        if (month == 4 and 10 <= current_date.day <= 24) or \
           (month == 6 and 15 <= current_date.day <= 30) or \
           (month == 10 and 12 <= current_date.day <= 26):
            is_exam_day = 1

        # Public / Festival Holidays
        is_holiday = 0
        if (month == 3 and current_date.day in [25]) or \
           (month == 4 and current_date.day in [14]) or \
           (month == 5 and current_date.day in [1]) or \
           (month == 8 and current_date.day in [15]) or \
           (month == 10 and current_date.day in [2, 20, 21, 22]):
            is_holiday = 1

        for item in MENU_ITEMS:
            item_id = item["item_id"]
            base = item["base_demand"]
            multiplier = 1.0

            # Day of week factor
            # University canteens: peak Tue-Thu, slightly lower Sat, much lower Sun
            if day_of_week in [1, 2, 3]: # Tue, Wed, Thu
                multiplier *= 1.10
            elif day_of_week == 0: # Mon
                multiplier *= 1.02
            elif day_of_week == 4: # Fri
                multiplier *= 1.05
            elif day_of_week == 5: # Sat
                multiplier *= 0.65
            elif day_of_week == 6: # Sun
                multiplier *= 0.40

            # Exam effect: quick bites & coffee surge by 30-40%, heavy thalis drop by 20%
            if is_exam_day:
                if item["category"] in ["Quick Bites", "Beverages"]:
                    multiplier *= 1.35
                elif item["category"] in ["Thali", "Main Course"]:
                    multiplier *= 0.82

            # Holiday effect: campus attendance drops
            if is_holiday:
                multiplier *= 0.35

            # Weather effects
            if rainfall > 10.0:
                if item["weather_sensitivity"] == "rain_boost":
                    multiplier *= 1.30 # Samosas, tea, hot snacks in the rain!
                elif item["category"] == "Beverages" and "Cold" in item["item_name"]:
                    multiplier *= 0.75
            
            if temperature > 32.0:
                if item["category"] == "Beverages":
                    multiplier *= 1.45
                elif item["weather_sensitivity"] == "cold_boost":
                    multiplier *= 0.85
            elif temperature < 16.0:
                if item["weather_sensitivity"] == "cold_boost":
                    multiplier *= 1.25
                elif item["category"] == "Beverages" and "Cold" in item["item_name"]:
                    multiplier *= 0.70

            # Promotions (5% chance of random promotional feature)
            is_promoted = 1 if (random.random() < 0.08 and not is_holiday) else 0
            if is_promoted:
                multiplier *= 1.22

            # Calculate actual demand with natural Gaussian noise
            demand_mean = base * multiplier
            noise = np.random.normal(0, base * 0.08)
            actual_demand = max(5, int(round(demand_mean + noise)))

            # Track history for trend
            history_list = history_tracker[item_id]
            trend_7d = round(float(np.mean(history_list[-7:])), 1) if len(history_list) >= 7 else round(float(base * 0.95), 1)
            trend_14d = round(float(np.mean(history_list[-14:])), 1) if len(history_list) >= 14 else round(float(base * 0.95), 1)
            history_list.append(actual_demand)

            # Simulated traditional manual kitchen intuition preparation (often overcooks by 15-25%!)
            # This is the "Before ZeroPlate" baseline comparison
            intuition_buffer = random.uniform(1.10, 1.30)
            traditional_prepared = int(round(base * intuition_buffer)) if not is_holiday else int(round(base * 0.7))
            traditional_surplus = max(0, traditional_prepared - actual_demand)

            records.append({
                "date": date_str,
                "day_of_week": day_of_week,
                "is_weekend": is_weekend,
                "is_holiday": is_holiday,
                "is_exam_day": is_exam_day,
                "temperature_c": temperature,
                "rainfall_mm": rainfall,
                "item_id": item_id,
                "item_name": item["item_name"],
                "category": item["category"],
                "meal_type": item["meal_type"],
                "base_price": item["base_price"],
                "prep_cost": item["prep_cost"],
                "trend_7d": trend_7d,
                "trend_14d": trend_14d,
                "is_promoted": is_promoted,
                "actual_demand": actual_demand,
                "traditional_prepared_qty": traditional_prepared,
                "traditional_surplus_waste": traditional_surplus
            })

    df = pd.DataFrame(records)
    return df

if __name__ == "__main__":
    output_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "canteen_sales_history.csv")
    
    print("Generating ZeroPlate historical dataset...")
    df = generate_contextual_dataset(start_date="2026-03-01", days=240)
    df.to_csv(csv_path, index=False)
    print(f"Dataset successfully created with {len(df)} rows across {df['item_name'].nunique()} menu items.")
    print(f"Saved to: {csv_path}")
    print("\nSample rows:")
    print(df.head(3)[["date", "item_name", "temperature_c", "rainfall_mm", "is_exam_day", "trend_7d", "actual_demand"]])
