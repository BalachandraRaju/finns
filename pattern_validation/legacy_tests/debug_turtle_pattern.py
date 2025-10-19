#!/usr/bin/env python3
"""
Debug the turtle breakout pattern to understand why it's not triggering.
"""

import sys
import os
sys.path.append('/Users/balachandra.raju/projects/finns')

from app.pattern_detector import PatternDetector, AlertType, PatternType
from app.test_patterns import generate_turtle_breakout_pattern
from app.charts import _calculate_pnf_points

def debug_turtle_pattern():
    """Debug why turtle breakout isn't triggering."""
    print("🔍 Debugging Turtle Breakout Pattern")
    print("=" * 50)
    
    # Generate test data
    candles = generate_turtle_breakout_pattern()
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    closes = [c['close'] for c in candles]
    
    print(f"📊 Generated {len(candles)} candles")
    print(f"   Price range: {min(lows):.0f} - {max(highs):.0f}")
    
    # Calculate P&F points
    box_pct = 0.01
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_pct, 3)
    
    print(f"\n📈 P&F Analysis:")
    print(f"   Generated {len(x_coords)} P&F points")
    print(f"   Total columns: {max(x_coords) if x_coords else 0}")
    
    # Analyze columns
    all_columns = sorted(set(x_coords))
    print(f"   Unique columns: {len(all_columns)}")
    print(f"   Columns: {all_columns}")
    
    # Check if we have 20+ columns for turtle pattern
    if len(all_columns) >= 20:
        print(f"   ✅ Sufficient columns for turtle pattern (need 20+)")
    else:
        print(f"   ❌ Insufficient columns for turtle pattern (have {len(all_columns)}, need 20+)")
    
    # Find X highs in each column
    x_column_highs = {}
    for i, (col, price, symbol) in enumerate(zip(x_coords, y_coords, pnf_symbols)):
        if symbol == 'X':
            if col not in x_column_highs or price > x_column_highs[col]:
                x_column_highs[col] = price
    
    print(f"\n📊 X Column Highs:")
    for col in sorted(x_column_highs.keys()):
        print(f"      Column {col}: {x_column_highs[col]:.2f}")
    
    # Check the last 20 columns (if we have them)
    if len(all_columns) >= 20:
        recent_20_columns = all_columns[-20:]
        print(f"\n🎯 Last 20 Columns: {recent_20_columns}")
        
        # Find highest X in last 20 columns
        highest_in_range = 0
        for col in recent_20_columns:
            if col in x_column_highs and x_column_highs[col] > highest_in_range:
                highest_in_range = x_column_highs[col]
        
        print(f"   Highest X in last 20 columns: {highest_in_range:.2f}")
        
        # Check latest column breakout
        latest_column = max(all_columns)
        latest_x_high = x_column_highs.get(latest_column, 0)
        
        print(f"   Latest column: {latest_column}")
        print(f"   Latest X high: {latest_x_high:.2f}")
        print(f"   Breakout condition: {latest_x_high:.2f} > {highest_in_range:.2f} = {latest_x_high > highest_in_range}")
    
    # Test pattern detection
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols, closes)
    
    print(f"\n🚨 Alert Analysis:")
    print(f"   Total alerts: {len(alerts)}")
    
    for alert in alerts:
        print(f"\n   🟢 Alert: {alert.alert_type.value}")
        print(f"      Pattern: {alert.pattern_type.value}")
        print(f"      Column: {alert.column}, Price: {alert.price:.2f}")
        print(f"      Reason: {alert.trigger_reason}")
    
    # Check specifically for turtle alerts
    turtle_alerts = [a for a in alerts if a.pattern_type == PatternType.TURTLE_BREAKOUT_BUY]
    print(f"\n🐢 Turtle Breakout Alerts: {len(turtle_alerts)}")
    
    if len(turtle_alerts) == 0:
        print("   ❌ No turtle breakout alerts found")
        print("   💡 Possible reasons:")
        print("      - Not enough columns (need 20+)")
        print("      - No breakout above 20-column high")
        print("      - Other patterns triggered first")
    
    return len(turtle_alerts) > 0

if __name__ == "__main__":
    debug_turtle_pattern()
