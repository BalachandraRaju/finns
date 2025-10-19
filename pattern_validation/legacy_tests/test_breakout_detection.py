#!/usr/bin/env python3
"""
Test script to verify the improved breakout detection logic.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.pattern_detector import PatternDetector, AlertType
from app.charts import _calculate_pnf_points

def test_simple_breakout():
    """Test simple breakout detection with clear data."""
    print("🧪 Testing Simple Breakout Detection")
    print("=" * 50)
    
    # Create simple test data with clear breakout
    highs = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 115]  # Clear breakout at 115
    lows =  [99,  100, 101, 102, 103, 104, 105, 106, 107, 108, 114]
    
    box_pct = 0.01
    reversal = 3
    
    # Calculate P&F points
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_pct, reversal)
    
    print(f"📊 P&F Data:")
    for i, (x, y, sym) in enumerate(zip(x_coords, y_coords, pnf_symbols)):
        print(f"  Column {x}: {sym} at {y:.2f}")
    
    # Test pattern detection
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols)
    
    print(f"\n🚨 Alerts Generated: {len(alerts)}")
    for alert in alerts:
        print(f"  Column {alert.column}: {alert.alert_type.value} - {alert.trigger_reason}")
    
    # Check if we got the expected breakout alert
    buy_alerts = [a for a in alerts if a.alert_type == AlertType.BUY]
    if buy_alerts:
        print(f"✅ SUCCESS: Found {len(buy_alerts)} BUY alert(s)")
        for alert in buy_alerts:
            print(f"   Alert at column {alert.column}, price {alert.price:.2f}")
    else:
        print("❌ FAILED: No BUY alerts found for breakout")
    
    return len(buy_alerts) > 0

def test_simple_breakdown():
    """Test simple breakdown detection with clear data."""
    print("\n🧪 Testing Simple Breakdown Detection")
    print("=" * 50)
    
    # Create simple test data with clear breakdown
    highs = [120, 119, 118, 117, 116, 115, 114, 113, 112, 111, 105]  # Clear breakdown at 105
    lows =  [119, 118, 117, 116, 115, 114, 113, 112, 111, 110, 104]
    
    box_pct = 0.01
    reversal = 3
    
    # Calculate P&F points
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_pct, reversal)
    
    print(f"📊 P&F Data:")
    for i, (x, y, sym) in enumerate(zip(x_coords, y_coords, pnf_symbols)):
        print(f"  Column {x}: {sym} at {y:.2f}")
    
    # Test pattern detection
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols)
    
    print(f"\n🚨 Alerts Generated: {len(alerts)}")
    for alert in alerts:
        print(f"  Column {alert.column}: {alert.alert_type.value} - {alert.trigger_reason}")
    
    # Check if we got the expected breakdown alert
    sell_alerts = [a for a in alerts if a.alert_type == AlertType.SELL]
    if sell_alerts:
        print(f"✅ SUCCESS: Found {len(sell_alerts)} SELL alert(s)")
        for alert in sell_alerts:
            print(f"   Alert at column {alert.column}, price {alert.price:.2f}")
    else:
        print("❌ FAILED: No SELL alerts found for breakdown")
    
    return len(sell_alerts) > 0

def test_bullish_breakout_pattern():
    """Test the specific bullish breakout pattern from test data."""
    print("\n🧪 Testing Bullish Breakout Pattern")
    print("=" * 50)
    
    from app.test_patterns import generate_bullish_breakout_pattern
    
    # Get the test pattern data
    candles = generate_bullish_breakout_pattern()
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    
    box_pct = 0.01
    reversal = 3
    
    # Calculate P&F points
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_pct, reversal)
    
    print(f"📊 Pattern has {len(x_coords)} P&F points")
    
    # Test pattern detection
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols)
    
    print(f"\n🚨 Alerts Generated: {len(alerts)}")
    for alert in alerts:
        print(f"  Column {alert.column}: {alert.alert_type.value} - {alert.trigger_reason}")
    
    # Check pattern states
    print(f"\n📊 Pattern States:")
    for pattern_type, state in detector.pattern_states.items():
        if state.is_confirmed:
            print(f"  {pattern_type.value}: ✅ Confirmed at {state.confirmation_price:.2f}")
        elif state.alert_fired:
            print(f"  {pattern_type.value}: 🚨 Alert fired")
    
    return len(alerts) > 0

def main():
    """Run all breakout detection tests."""
    print("🔍 Testing Improved Breakout Detection Logic")
    print("=" * 60)
    
    test1 = test_simple_breakout()
    test2 = test_simple_breakdown()
    test3 = test_bullish_breakout_pattern()
    
    print("\n" + "=" * 60)
    print("📋 Test Results Summary:")
    print(f"  Simple Breakout: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"  Simple Breakdown: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"  Bullish Pattern: {'✅ PASS' if test3 else '❌ FAIL'}")
    
    if all([test1, test2, test3]):
        print("\n🎉 All tests passed! Breakout detection is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the logic above.")

if __name__ == "__main__":
    main()
