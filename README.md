# ZeroPlate: An AI-Powered Platform for Predictive Food Demand Forecasting and Surplus Redistribution

> **A Major Project Synopsis Implementation**  
> **Candidate:** Yogesh Vyas (University Roll No: `2106389`)  
> **Degree:** Bachelor's of Computer Applications (`BCA [AI & DS]`)  
> **Under the Guidance of:** Ms. Shivani Sharma, Assistant Professor  
> **Department:** Department of Computer Applications  
> **Institution:** Graphic Era (Deemed to be University), Dehradun, Uttarakhand  
> **Academic Session:** 2026  

---

## 1. Executive Summary & Core Philosophy

Commercial restaurants, school and college cafeterias, and institutional catering operations constantly prepare more food than gets consumed. This overproduction is not typically due to careless kitchen staff, but rather because **there has been no dependable, data-driven method for predicting the exact number of portions required on any given day**. 

Kitchen staff traditionally rely on intuition, guesswork, and informal rules-of-thumb, frequently adding an arbitrary **15% to 25% overproduction buffer** to avoid running out of meals. This leads to:
1. **Severe Food Waste:** Ingredients, water, energy, and labor wasted before the food even reaches a plate.
2. **Financial Losses:** Significant margin erosion from discarded raw materials and unmonetized prepared food.
3. **Late-Stage Interventions:** Existing food rescue applications (such as *Too Good To Go*) only intervene **after** the surplus is cooked—after ingredients, manpower, gas, and electricity have already been consumed.

### The ZeroPlate Principle: "Prevention Before Cure"
ZeroPlate shifts the intervention point to the start of the food lifecycle through a continuous operational loop:
1. **Forecast:** Anticipate item-level demand *before production commences* using contextual tree-based machine learning regression.
2. **Plan:** Deliver recommended cooking quantities and raw ingredient weights to kitchen staff, eliminating the 25% intuition overproduction buffer at its source.
3. **Redistribute:** When unavoidable surplus occurs, automatically escalate it through a prioritized **3-Tier Recovery Pipeline**:
   - **Tier 1:** Student Marketplace (Discounted 'Surprise Boxes' near closing time)
   - **Tier 2:** Verified NGO Donation (Automated dispatch to Robin Hood Army / Feeding India with secure PIN handover)
   - **Tier 3:** Campus Bio-Composting (100% landfill diversion into nutrient organic fertilizer)

---

## 2. One Platform Connects Prediction to Action: The 5-Step Loop

```
  [01. Collect] ──> [02. Predict] ──> [03. Plan] ──> [04. Monitor] ──> [05. Redistribute]
  Sales History      ML Regression     Portion Targets  Surplus Check    Tier 1: Student Market
  Weather, Exams     Random Forest     Raw Ingredients  Real-Time Sales  Tier 2: NGO Rescue
  7d/14d Trends      Gradient Boost    Checklist        Closing Window   Tier 3: Bio-Composting
```

---

## 3. Machine Learning Formulation & Evaluation (Section 5.2)

Demand is modeled as an **item-level regression problem** utilizing multi-source contextual variables:
- **Calendar & Academic Context:** Day of week, weekend indicator, public holidays, and **Graphic Era University exam schedules** (which spike coffee and snacks while reducing heavy thali demand).
- **Dehradun Weather Context:** Daily temperature (°C) and precipitation/rainfall (mm).
- **Time-Series Momentum:** Rolling 7-day (`trend_7d`) and 14-day (`trend_14d`) sales moving averages.
- **Menu Factors:** Dish category, meal type (Breakfast, Lunch, Snacks, Dinner), base price, and active promotions.

### Evaluation Metric: Root Mean Squared Error (RMSE)
$$\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (p_i - a_i)^2}$$

Where:
- $p_i$ is the predicted demand for item observation $i$.
- $a_i$ is the actual quantity consumed for item observation $i$.
- $n$ is the total count of test observations.

### Empirical Model Benchmark Results
Evaluated on 2,400 item-day records across Graphic Era canteen catalog:

| Model Architecture | RMSE (Portions) | MAE (Portions) | $R^2$ Score | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Manual Intuition Baseline** (7-day MA) | `40.44` | `31.90` | `0.381` | Traditional Guesswork |
| **Random Forest Regressor (RFR)** | `16.25` | `10.67` | `0.900` | Tree Ensemble |
| **Gradient Boosting Regressor (GBR)** | **`12.53`** | **`9.27`** | **`0.941`** | **Champion Model** |

> **Key Finding:** ZeroPlate's Gradient Boosting Regressor achieves a **69.0% reduction in forecasting error** compared to traditional manual kitchen intuition.

---

## 4. Surplus Redistribution Logic & Pseudocode (Section 5.3)

Implemented directly in `app/escalation_engine.py`:

```pascal
Input: predicted_qty, actual_sold, time_remaining, threshold begin
 remaining_stock = predicted_qty - actual_sold
 if time_remaining < closing_window and remaining_stock > threshold then 
   list item as discounted 'surprise box' on student marketplace 
 end if
 if item unsold at closing_time then
   notify nearest verified NGO with quantity and pickup window 
 end if 
 if item not collected by NGO within pickup window then 
   route item to composting / waste-management channel 
 end if 
end
```

### The Three Escalation Tiers:
1. **Tier 1 — Student Marketplace:**
   When `time_remaining < closing_window` (default 90 mins) and `remaining_stock > threshold` (default 8 units), items are automatically published to the Student Marketplace as **55% discounted "Surprise Meal Boxes"**. Students reserve items and receive a verifiable digital token (e.g., `ZP-TK-4921`) for canteen counter collection.
2. **Tier 2 — NGO Donation Coordination:**
   At closing time, any remaining unreserved meals are escalated to verified local non-profit partners (e.g., **Robin Hood Army Dehradun Chapter**, **Feeding India GEU Chapter**). Coordinators receive portion counts, temperature/safety notes, a **60-minute pickup deadline**, and a 4-digit staff verification PIN.
3. **Tier 3 — Composting and Waste Routing:**
   If food is not collected within the safe thermal pickup window or for vegetable prep scraps, the batch is routed to the **Graphic Era Campus Bio-Compost Facility / Green Digester Unit 2**. Records track kilograms diverted, compost yield (kg), and landfill methane abatement ($2.5 \times$ CO₂e factor).

---

## 5. System Modules (Section 5.4)

| # | Module | Route | Key Capabilities |
| :--- | :--- | :--- | :--- |
| **1** | **Demand Prediction Dashboard** | `/forecast` | Live ML predictions, RMSE scoreboard, feature importances, interactive prediction playground. |
| **2** | **Inventory & Production Planning** | `/production` | Recommended cooking targets, raw ingredient calculator, morning prep SOP checklist. |
| **3** | **Student Surplus Marketplace** | `/marketplace` | Discounted surprise boxes, active countdowns, student reservations, redemption tokens. |
| **4** | **NGO Donation Coordination** | `/ngo` | Automated closing escalation, verified NGOs directory, dispatch claim, PIN verification. |
| **5** | **Composting & Waste Routing** | `/composting` | Bio-compost audit logs, net weight, organic fertilizer yield, official diversion certificate. |
| **6** | **Analytics & Reporting** | `/analytics` | Food waste avoided (kg & %), cost savings (₹), meals redistributed, before-vs-after ledger. |
| **–** | **Simulation & Demo Controller** | `/simulation` | Interactive time-warp controller to demonstrate morning, lunch, closing, and escalation triggers. |

---

## 6. Technology Stack (Chapter 4)

- **Backend:** Python 3.12 or newer, Flask 3.x
- **Machine Learning & Data Science:** Scikit-learn (RandomForestRegressor, GradientBoostingRegressor), Pandas, NumPy, Joblib
- **Database:** SQLite (local zero-configuration embedded DB) + `schema_mysql.sql` (production MySQL schema)
- **Frontend:** HTML5, Modern CSS, Tailwind CSS (CDN), Chart.js (Interactive visual charts), Lucide Icons
- **Deployment & Version Control:** Git, GitHub, Vercel-ready structure

---

## 7. Directory Structure

```
zeroplate/
├── data/
│   ├── generate_dataset.py       # Simulates 2,400 canteen sales records with weather & exams
│   ├── canteen_sales_history.csv # Synthetic training dataset
│   └── zeroplate.db              # SQLite operational database
├── models/
│   ├── train.py                  # Model training and RMSE evaluation script
│   ├── predict.py                # Model inference pipeline & safety buffer calculator
│   ├── model_rf.pkl              # Saved Random Forest Regressor
│   ├── model_gb.pkl              # Saved Gradient Boosting Regressor (Champion)
│   ├── model_metrics.json        # Serialized evaluation metrics & feature importances
│   └── feature_meta.json         # Feature encoding metadata
├── app/
│   ├── __init__.py               # Flask application factory
│   ├── config.py                 # Application configuration
│   ├── database.py               # SQLite schema & seed loader
│   ├── escalation_engine.py      # Section 5.3 Surplus Escalation Engine
│   ├── seed_demo.py              # Operational day seed generator
│   ├── routes/
│   │   ├── dashboard.py          # Landing, Forecast, Production, Simulation routes
│   │   ├── marketplace.py        # Student Marketplace routes (Tier 1)
│   │   ├── ngo.py                # NGO Coordination routes (Tier 2)
│   │   ├── composting.py         # Composting & Waste Routing routes (Tier 3)
│   │   ├── analytics.py          # Analytics & Reporting routes (Module 6)
│   │   └── api.py                # REST API endpoints (prediction, claims, verification)
│   ├── static/
│   │   ├── css/style.css         # Custom responsive styling and animations
│   │   └── js/main.js            # Interactivity, toasts, modals, and simulation triggers
│   └── templates/
│       ├── base.html             # Sleek navigation header, footer & academic metadata
│       ├── index.html            # Landing page & continuous operating loop
│       ├── forecast.html         # Module 1: Demand Prediction Dashboard
│       ├── production.html       # Module 2: Inventory & Kitchen Planning
│       ├── marketplace.html      # Module 3: Student Surplus Marketplace
│       ├── ngo.html              # Module 4: NGO Donation Coordination
│       ├── composting.html       # Module 5: Composting & Waste Routing
│       ├── analytics.html        # Module 6: Analytics & Impact Reporting
│       └── simulation.html       # Interactive Demo Controller
├── tests/
│   ├── test_models.py            # Unit tests for ML forecaster and RMSE
│   ├── test_pipeline.py          # Unit tests for 3-tier escalation engine
│   └── test_api.py               # Integration tests for all web routes & REST APIs
├── schema_mysql.sql              # MySQL DDL schema for enterprise deployment
├── requirements.txt              # Python library dependencies
├── run.py                        # Web application server entry point
└── README.md                     # Comprehensive academic & technical documentation
```

---

## 8. Installation & Quick Start

### 1. Prerequisites
Ensure Python 3.10+ is installed on your machine.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Generate Historical Data & Train ML Models (Optional - Models Are Already Included)
```bash
# Generate 2,400 records of canteen sales history
python data/generate_dataset.py

# Train Random Forest and Gradient Boosting Regressors
python models/train.py
```

### 4. Load Mentor Demo Data (Recommended for a Project Walkthrough)\nRun this after installing dependencies and before starting the server:\n\n```bash\npython app/seed_demo.py\n```\n\nThe loader creates a sample operating day using the saved demand model. It adds menu plans, kitchen sales, discounted listings, sample reservations, donation records in different stages, and compost batches. It does not delete existing orders or other dates. If the selected date already has plans, it leaves the database unchanged. To use a different date, run `python app/seed_demo.py --date YYYY-MM-DD`.\n\nThe demo names, IDs, reservations, PINs and quantities are illustrative records for presentation only; they are not real customer transactions. The loader prints the demo PIN needed to demonstrate a claimed donation.\n\n### 5. Run Automated Test Suite
```bash
python tests/test_models.py
python tests/test_pipeline.py
python tests/test_api.py
```

### 6. Launch the ZeroPlate Platform
```bash
python run.py
```

Open your web browser and navigate to:
**`http://127.0.0.1:5000/`**

---

## 9. Mentor Demonstration Guide

After loading the mentor demo data and launching the app, use this simple walkthrough:

1. **Overview (`/`):** Introduce the food-planning and recovery workflow. Point out the menu plan, active discounted listings, donations and compost records.
2. **Demand planning (`/forecast`):** Show the predicted servings for each menu item. Change the menu item, day, weather and recent sales value in the estimate form, then click **Estimate servings**.
3. **Kitchen plan (`/production`):** Compare suggested preparation with prepared, sold and remaining servings. Explain that ingredient quantities are estimates, not live stock readings.
4. **Discounted meals (`/marketplace`):** Show the active discounted meal offers, original prices, reduced prices, remaining quantities and collection deadlines. The demo loader adds sample reservations so analytics has activity to display.
5. **Community donations (`/ngo`):** Show the pending, assigned and collected examples. To demonstrate collection verification for the sample claimed donation, use the PIN printed by the seed script in the terminal.
6. **Compost tracking (`/composting`):** Show the sample compost batches and the estimated compost and emissions figures.
7. **Operations analytics (`/analytics`):** Explain prepared versus sold servings, reservation value, recovered meals, compost quantity and the estimated comparison figures.

The mentor demo data is illustrative. Explain that the sample names, IDs, quantities, reservations and recovery records are provided to make the project screens demonstrable; they are not live transactions from a real canteen.
