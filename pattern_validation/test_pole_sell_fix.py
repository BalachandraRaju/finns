#!/usr/bin/env python3
"""
Test pole follow through sell pattern fix.
"""

import sys
import os
sys.path.append('/Users/balachandra.raju/projects/finns')

from app.test_patterns import generate_pole_follow_through_sell_pattern
from app.charts import _calculate_pnf_points

def test_pole_sell():
    """Test pole follow through sell pattern."""
    print("🧪 Testing Pole Follow Through Sell Pattern")
    print("=" * 50)
    
    # Generate test data
    candles = generate_pole_follow_through_sell_pattern()
    print(f"📊 Generated {len(candles)} candles")
    print(f"📊 First candle: {candles[0]}")
    print(f"📊 Data types: open={type(candles[0]['open'])}, high={type(candles[0]['high'])}")
    
    # Extract price data
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    
    print(f"📊 Testing P&F calculation...")
    try:
        x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, 0.0025, 3)
        print(f"✅ SUCCESS: Generated {len(x_coords)} P&F points")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    test_pole_sell()
