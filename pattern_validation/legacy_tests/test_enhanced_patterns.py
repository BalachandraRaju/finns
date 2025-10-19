#!/usr/bin/env python3
"""
Test the enhanced pattern detection with EMA validation, turtle breakouts, and anchor columns.
"""

import sys
import os
sys.path.append('/Users/balachandra.raju/projects/finns')

from app.pattern_detector import PatternDetector, AlertType, PatternType
from app.test_patterns import (
    generate_turtle_breakout_pattern, 
    generate_anchor_breakout_pattern,
    generate_ema_validated_triple_top_pattern,
    TEST_PATTERNS
)
from app.charts import _calculate_pnf_points

def test_turtle_breakout():
    """Test turtle breakout pattern detection."""
    print("🐢 Testing Turtle Breakout Pattern")
    print("=" * 50)
    
    # Generate test data
    candles = generate_turtle_breakout_pattern()
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    closes = [c['close'] for c in candles]
    
    print(f"📊 Generated {len(candles)} candles")
    print(f"   Price range: {min(lows):.0f} - {max(highs):.0f}")
    print(f"   Expected: 20-column range breakout above 111")
    
    # Calculate P&F points
    box_pct = 0.01
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_pct, 3)
    
    print(f"\n📈 P&F Analysis:")
    print(f"   Generated {len(x_coords)} P&F points")
    print(f"   Columns: {max(x_coords) if x_coords else 0}")
    
    # Test pattern detection with EMA
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols, closes)
    
    print(f"\n🚨 Alert Analysis:")
    print(f"   Total alerts: {len(alerts)}")
    
    turtle_alerts = [a for a in alerts if 'TURTLE' in a.trigger_reason]
    print(f"   Turtle breakout alerts: {len(turtle_alerts)}")
    
    for alert in alerts:
        print(f"\n   🟢 Alert: {alert.alert_type.value}")
        print(f"      Pattern: {alert.pattern_type.value}")
        print(f"      Column: {alert.column}, Price: {alert.price:.2f}")
        print(f"      Reason: {alert.trigger_reason}")
    
    return len(turtle_alerts) > 0

def test_anchor_breakout():
    """Test anchor column breakout pattern detection."""
    print("\n⚓ Testing Anchor Column Breakout Pattern")
    print("=" * 50)
    
    # Generate test data
    candles = generate_anchor_breakout_pattern()
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    closes = [c['close'] for c in candles]
    
    print(f"📊 Generated {len(candles)} candles")
    print(f"   Price range: {min(lows):.0f} - {max(highs):.0f}")
    print(f"   Expected: Anchor column (14+ bars) breakout above 120")
    
    # Calculate P&F points
    box_pct = 0.01
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_pct, 3)
    
    print(f"\n📈 P&F Analysis:")
    print(f"   Generated {len(x_coords)} P&F points")
    print(f"   Columns: {max(x_coords) if x_coords else 0}")
    
    # Analyze column heights
    column_heights = {}
    for i, (col, price, symbol) in enumerate(zip(x_coords, y_coords, pnf_symbols)):
        if col not in column_heights:
            column_heights[col] = 0
        column_heights[col] += 1
    
    print(f"\n📏 Column Heights:")
    for col in sorted(column_heights.keys()):
        height = column_heights[col]
        anchor_status = "⚓ ANCHOR" if height >= 14 else ""
        print(f"      Column {col}: {height} bars {anchor_status}")
    
    # Test pattern detection
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols, closes)
    
    print(f"\n🚨 Alert Analysis:")
    print(f"   Total alerts: {len(alerts)}")
    
    anchor_alerts = [a for a in alerts if 'ANCHOR' in a.trigger_reason]
    print(f"   Anchor breakout alerts: {len(anchor_alerts)}")
    
    for alert in alerts:
        print(f"\n   🟢 Alert: {alert.alert_type.value}")
        print(f"      Pattern: {alert.pattern_type.value}")
        print(f"      Column: {alert.column}, Price: {alert.price:.2f}")
        print(f"      Reason: {alert.trigger_reason}")
    
    return len(anchor_alerts) > 0

def test_ema_validated_pattern():
    """Test EMA-validated triple top pattern."""
    print("\n📈 Testing EMA-Validated Triple Top Pattern")
    print("=" * 50)
    
    # Generate test data
    candles = generate_ema_validated_triple_top_pattern()
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    closes = [c['close'] for c in candles]
    
    print(f"📊 Generated {len(candles)} candles")
    print(f"   Price range: {min(lows):.0f} - {max(highs):.0f}")
    print(f"   Expected: Triple top with EMA validation")
    
    # Calculate 20 EMA manually for verification
    if len(closes) >= 20:
        multiplier = 2 / (20 + 1)
        ema = sum(closes[:20]) / 20
        for price in closes[20:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        print(f"   Final 20 EMA: {ema:.2f}")
        print(f"   Final price: {closes[-1]:.2f}")
        print(f"   Above EMA: {'✅ YES' if closes[-1] > ema else '❌ NO'}")
    
    # Calculate P&F points
    box_pct = 0.01
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_pct, 3)
    
    print(f"\n📈 P&F Analysis:")
    print(f"   Generated {len(x_coords)} P&F points")
    print(f"   Columns: {max(x_coords) if x_coords else 0}")
    
    # Test pattern detection with EMA
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols, closes)
    
    print(f"\n🚨 Alert Analysis:")
    print(f"   Total alerts: {len(alerts)}")
    
    ema_alerts = [a for a in alerts if 'EMA VALIDATED' in a.trigger_reason]
    triple_alerts = [a for a in alerts if 'TRIPLE TOP' in a.trigger_reason]
    
    print(f"   EMA-validated alerts: {len(ema_alerts)}")
    print(f"   Triple top alerts: {len(triple_alerts)}")
    
    for alert in alerts:
        print(f"\n   🟢 Alert: {alert.alert_type.value}")
        print(f"      Pattern: {alert.pattern_type.value}")
        print(f"      Column: {alert.column}, Price: {alert.price:.2f}")
        print(f"      Reason: {alert.trigger_reason}")
    
    return len(ema_alerts) > 0 or len(triple_alerts) > 0

def test_all_new_patterns():
    """Test all new pattern types in TEST_PATTERNS."""
    print("\n🧪 Testing All New Pattern Types")
    print("=" * 50)
    
    new_patterns = ['turtle_breakout', 'anchor_breakout', 'ema_triple_top']
    
    for pattern_name in new_patterns:
        if pattern_name in TEST_PATTERNS:
            print(f"\n📊 Testing: {TEST_PATTERNS[pattern_name]['name']}")
            
            try:
                # Generate test data
                candles = TEST_PATTERNS[pattern_name]['data_generator']()
                highs = [c['high'] for c in candles]
                lows = [c['low'] for c in candles]
                closes = [c['close'] for c in candles]
                
                # Calculate P&F points
                x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, 0.01, 3)
                
                # Test pattern detection
                detector = PatternDetector()
                alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols, closes)
                
                print(f"   ✅ Generated {len(alerts)} alerts")
                
                for alert in alerts:
                    print(f"      🚨 {alert.alert_type.value}: {alert.pattern_type.value}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        else:
            print(f"   ⚠️ Pattern '{pattern_name}' not found in TEST_PATTERNS")

if __name__ == "__main__":
    print("🔧 Testing Enhanced Pattern Detection System")
    print("=" * 80)
    
    # Test individual patterns
    test1_passed = test_turtle_breakout()
    test2_passed = test_anchor_breakout()
    test3_passed = test_ema_validated_pattern()
    
    # Test all new patterns
    test_all_new_patterns()
    
    print(f"\n🎯 Final Results:")
    print(f"   Turtle Breakout: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   Anchor Breakout: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"   EMA Validated: {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed and test3_passed:
        print(f"\n🎉 ALL ENHANCED PATTERNS WORKING! Ready for trading.")
    else:
        print(f"\n⚠️ Some patterns need attention.")
