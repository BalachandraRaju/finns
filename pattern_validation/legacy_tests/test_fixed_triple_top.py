#!/usr/bin/env python3
"""
Test the fixed triple top pattern detection logic.
"""

import sys
import os
sys.path.append('/Users/balachandra.raju/projects/finns')

from app.pattern_detector import PatternDetector, AlertType
from app.test_patterns import generate_triple_top_pattern
from app.charts import _calculate_pnf_points

def test_triple_top_detection():
    """Test that triple top pattern only triggers when there are 3 distinct similar tops."""
    
    print("🧪 Testing Fixed Triple Top Pattern Detection")
    print("=" * 60)
    
    # Generate the test pattern data
    candles = generate_triple_top_pattern()
    
    # Extract price data
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    
    print(f"📊 Generated {len(candles)} candles")
    print(f"   Price range: {min(lows):.0f} - {max(highs):.0f}")
    
    # Analyze the pattern structure
    # The pattern should have 3 tops at level 110
    tops_at_110 = [h for h in highs if h >= 110]
    print(f"   Highs at/above 110: {len(tops_at_110)} (should be 3 for triple top)")
    
    # Calculate P&F points
    box_pct = 0.01  # 1%
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_pct, 3)
    
    print(f"\n📈 P&F Analysis:")
    print(f"   Generated {len(x_coords)} P&F points")
    print(f"   Columns: {max(x_coords) if x_coords else 0}")
    
    if x_coords:
        x_count = sum(1 for s in pnf_symbols if s == 'X')
        o_count = sum(1 for s in pnf_symbols if s == 'O')
        print(f"   X's: {x_count}, O's: {o_count}")
        
        # Show X columns and their highest points
        x_columns = {}
        for i, (col, price, symbol) in enumerate(zip(x_coords, y_coords, pnf_symbols)):
            if symbol == 'X':
                if col not in x_columns or price > x_columns[col]:
                    x_columns[col] = price
        
        print(f"\n📋 X Column Highs:")
        for col in sorted(x_columns.keys()):
            print(f"      Column {col}: {x_columns[col]:.0f}")
        
        # Count similar highs (within 1% of 110)
        similar_highs = []
        for price in x_columns.values():
            if abs(price - 110) <= 110 * 0.01:  # Within 1% of 110
                similar_highs.append(price)
        
        print(f"\n🎯 Pattern Analysis:")
        print(f"   Similar highs near 110: {len(similar_highs)} (should be 3)")
        print(f"   Similar high values: {similar_highs}")
        
        if len(similar_highs) == 3:
            print(f"   ✅ Triple top formation confirmed!")
        else:
            print(f"   ⚠️ Not a proper triple top formation")
    
    # Test pattern detection
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols)
    
    print(f"\n🚨 Alert Analysis:")
    print(f"   Total alerts generated: {len(alerts)}")
    
    triple_top_alerts = [a for a in alerts if 'TRIPLE TOP' in a.trigger_reason]
    buy_alerts = [a for a in alerts if a.alert_type == AlertType.BUY]
    
    print(f"   Triple top alerts: {len(triple_top_alerts)}")
    print(f"   Buy alerts: {len(buy_alerts)}")
    
    for alert in alerts:
        print(f"\n   🟢 Alert: {alert.alert_type.value}")
        print(f"      Column: {alert.column}")
        print(f"      Price: {alert.price:.2f}")
        print(f"      Reason: {alert.trigger_reason}")
    
    # Validation
    print(f"\n✅ Validation Results:")
    
    if len(triple_top_alerts) == 1:
        print(f"   ✅ Correct: Exactly 1 triple top alert generated")
    elif len(triple_top_alerts) == 0:
        print(f"   ❌ Error: No triple top alert generated (should be 1)")
    else:
        print(f"   ❌ Error: {len(triple_top_alerts)} triple top alerts (should be 1)")
    
    if len(similar_highs) == 3 and len(triple_top_alerts) == 1:
        print(f"   ✅ Perfect: 3 similar tops detected and 1 alert fired")
    elif len(similar_highs) != 3:
        print(f"   ⚠️ Pattern issue: {len(similar_highs)} similar tops (should be 3)")
    
    return len(triple_top_alerts) == 1 and len(similar_highs) == 3

def test_false_positive_case():
    """Test that alerts don't fire when tops are not at similar levels."""
    
    print("\n🧪 Testing False Positive Prevention")
    print("=" * 60)
    
    # Create data with tops at different levels (should NOT trigger triple top)
    highs = [100, 105, 110, 108, 115, 112, 120, 118, 125]  # Different levels
    lows = [95, 100, 105, 103, 110, 107, 115, 113, 120]
    
    print(f"📊 Test data with different top levels:")
    print(f"   Highs: {highs}")
    print(f"   No similar tops at same level")
    
    # Calculate P&F points
    box_pct = 0.01
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_pct, 3)
    
    # Test pattern detection
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols)
    
    triple_top_alerts = [a for a in alerts if 'TRIPLE TOP' in a.trigger_reason]
    
    print(f"\n🚨 Alert Analysis:")
    print(f"   Triple top alerts: {len(triple_top_alerts)} (should be 0)")
    
    if len(triple_top_alerts) == 0:
        print(f"   ✅ Correct: No false positive triple top alerts")
        return True
    else:
        print(f"   ❌ Error: False positive alerts generated")
        for alert in triple_top_alerts:
            print(f"      {alert.trigger_reason}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Fixed Triple Top Pattern Detection Logic")
    print("=" * 80)
    
    # Test 1: Proper triple top should trigger alert
    test1_passed = test_triple_top_detection()
    
    # Test 2: Different levels should NOT trigger alert
    test2_passed = test_false_positive_case()
    
    print(f"\n🎯 Final Results:")
    print(f"   Test 1 (Proper Triple Top): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   Test 2 (False Positive Prevention): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print(f"\n🎉 ALL TESTS PASSED! Triple top detection is working correctly.")
    else:
        print(f"\n⚠️ Some tests failed. Pattern detection needs further fixes.")
