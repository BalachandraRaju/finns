#!/usr/bin/env python3
"""
Debug catapult sell pattern detection.
"""

import sys
import os
sys.path.append('/Users/balachandra.raju/projects/finns')

from app.test_patterns import generate_catapult_sell_pattern
from app.charts import _calculate_pnf_points
from app.pattern_detector import PatternDetector, PatternType

def debug_catapult_sell():
    """Debug why catapult sell pattern is not being detected."""
    print("🔍 DEBUGGING CATAPULT SELL PATTERN")
    print("=" * 50)
    
    # Generate test data
    candles = generate_catapult_sell_pattern()
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    closes = [c['close'] for c in candles]
    
    print(f"📊 Generated {len(candles)} candles")
    print(f"📊 Price range: {min(lows):.2f} - {max(highs):.2f}")
    
    # Calculate P&F points
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, 0.01, 3)
    
    print(f"📊 Generated {len(x_coords)} P&F points")
    
    # Analyze latest column
    latest_column = max(x_coords)
    print(f"📊 Latest column: {latest_column}")
    
    # Find points in latest column
    latest_points = []
    for i in range(len(x_coords)):
        if x_coords[i] == latest_column:
            latest_points.append((i, y_coords[i], pnf_symbols[i]))
    
    print(f"📊 Points in latest column: {len(latest_points)}")
    
    # Check O symbols in latest column
    o_symbols = [point for point in latest_points if point[2] == 'O']
    print(f"📊 O symbols in latest column: {len(o_symbols)}")
    
    if o_symbols:
        lowest_o = min(point[1] for point in o_symbols)
        print(f"📊 Lowest O price in latest column: {lowest_o:.2f}")
        
        # Find previous O lows
        previous_o_lows = []
        for i in range(len(x_coords)):
            if pnf_symbols[i] == 'O' and x_coords[i] < latest_column:
                previous_o_lows.append(y_coords[i])
        
        if previous_o_lows:
            support_level = min(previous_o_lows)
            print(f"📊 Previous support level: {support_level:.2f}")
            print(f"📊 Catapult condition (O < support): {lowest_o < support_level}")
        
        # Find X column highs for resistance
        x_column_highs = {}
        for i in range(len(x_coords)):
            if pnf_symbols[i] == 'X' and x_coords[i] < latest_column:
                col = x_coords[i]
                if col not in x_column_highs or y_coords[i] > x_column_highs[col]:
                    x_column_highs[col] = y_coords[i]
        
        if x_column_highs:
            resistance_level = max(x_column_highs.values())
            tolerance = resistance_level * 0.02
            similar_highs = [high for high in x_column_highs.values()
                           if abs(high - resistance_level) <= tolerance]
            
            print(f"📊 Resistance level: {resistance_level:.2f}")
            print(f"📊 Similar highs count: {len(similar_highs)}")
            print(f"📊 Triple top condition (>=3): {len(similar_highs) >= 3}")
    
    # Test pattern detection
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols, closes)
    
    print(f"\n🚨 ALERTS GENERATED:")
    print(f"   Total alerts: {len(alerts)}")
    
    catapult_sell_alerts = [a for a in alerts if a.pattern_type == PatternType.CATAPULT_SELL]
    print(f"   Catapult Sell alerts: {len(catapult_sell_alerts)}")
    
    for alert in alerts:
        print(f"   🚨 {alert.alert_type.value}: {alert.pattern_type.value} at {alert.price:.2f}")
        if alert.pattern_type == PatternType.CATAPULT_SELL:
            print(f"      Reason: {alert.trigger_reason}")

if __name__ == "__main__":
    debug_catapult_sell()
