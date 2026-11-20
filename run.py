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
    print("  Food demand planning and surplus recovery")
    print("=" * 65)
    print(f"  * Server running at: http://127.0.0.1:{port}/")
    print(f"  * Owner menu:   http://127.0.0.1:{port}/owner")
    print(f"  * Forecast:    http://127.0.0.1:{port}/forecast")
    print(f"  * Kitchen plan:  http://127.0.0.1:{port}/production")
    print(f"  * Surplus market: http://127.0.0.1:{port}/marketplace")
    print(f"  * Donations:  http://127.0.0.1:{port}/ngo")
    print(f"  * Compost tracking:     http://127.0.0.1:{port}/composting")
    print(f"  * Analytics:   http://127.0.0.1:{port}/analytics")
    print(f"  * Simulation:  http://127.0.0.1:{port}/simulation")
    print("=" * 65)
    app.run(host="0.0.0.0", port=port, debug=False)
