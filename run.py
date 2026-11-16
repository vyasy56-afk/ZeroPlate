"""
ZeroPlate: Application Server Entry Point
Run this script to launch the ZeroPlate web platform.
"""

import os
import sys

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 65)
    print("  ZeroPlate: AI Demand Forecasting & Surplus Redistribution")
    print("  Project Synopsis by Yogesh Vyas · 2106389 · BCA (AI & DS)")
    print("  Graphic Era (Deemed to be University), Dehradun")
    print("=" * 65)
    print(f"  * Server running at: http://127.0.0.1:{port}/")
    print("  * Module 1 (Forecast):    http://127.0.0.1:{port}/forecast")
    print("  * Module 2 (Production):  http://127.0.0.1:{port}/production")
    print("  * Module 3 (Marketplace): http://127.0.0.1:{port}/marketplace")
    print("  * Module 4 (NGO Rescue):  http://127.0.0.1:{port}/ngo")
    print("  * Module 5 (Compost):     http://127.0.0.1:{port}/composting")
    print("  * Module 6 (Analytics):   http://127.0.0.1:{port}/analytics")
    print("  * Simulation Controller:  http://127.0.0.1:{port}/simulation")
    print("=" * 65)
    app.run(host="127.0.0.1", port=port, debug=False)
