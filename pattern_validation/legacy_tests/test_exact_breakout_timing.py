#!/usr/bin/env python3
"""
Test script to verify alerts fire at the EXACT breakout moment, not column end.
Tests the specific scenario: X column 100->101->109, alert should fire at 101.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.pattern_detector import PatternDetector, AlertType
from app.charts import _calculate_pnf_points

def test_exact_breakout_scenario():
    """Test the exact scenario described: alert at 101, not 109."""
    print("🎯 Testing EXACT Breakout Timing")
    print("Scenario: X column 100->101->109, alert should fire at 101")
    print("=" * 60)
    
    # Create the exact scenario described
    # First X column goes to 100, then O column, then new X column 101->109
    highs = [95, 96, 97, 98, 99, 100,  # First X column to 100
             99, 98, 97, 96, 95,        # O column down
             96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109]  # New X column 101->109
    
    lows =  [94, 95, 96, 97, 98, 99,   # First X column
             98, 97, 96, 95, 94,        # O column down  
             95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108]   # New X column
    
    box_pct = 0.01
    reversal = 3
    
    # Calculate P&F points
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_pct, reversal)
    
    print(f"📊 P&F Chart Analysis:")
    print(f"Total points: {len(x_coords)}")
    
    # Show the chart structure
    columns = {}
    for i, (x, y, sym) in enumerate(zip(x_coords, y_coords, pnf_symbols)):
        if x not in columns:
            columns[x] = []
        columns[x].append((y, sym, i))
    
    for col_num in sorted(columns.keys()):
        points = columns[col_num]
        symbol = points[0][1]
        prices = [p[0] for p in points]
        min_price, max_price = min(prices), max(prices)
        print(f"  Column {col_num}: {symbol} from {min_price:.2f} to {max_price:.2f} ({len(points)} points)")
    
    # Test pattern detection
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols)
    
    print(f"\n🚨 Alerts Generated: {len(alerts)}")
    
    for alert in alerts:
        print(f"  Column {alert.column}: {alert.alert_type.value} at {alert.price:.2f}")
        print(f"    Reason: {alert.trigger_reason}")
    
    # Find the breakout alert
    buy_alerts = [a for a in alerts if a.alert_type == AlertType.BUY]
    
    if buy_alerts:
        breakout_alert = buy_alerts[0]  # Should be first (and only) BUY alert
        
        # Check if alert fired at the right moment (around 101, not 109)
        if 100.5 <= breakout_alert.price <= 102:
            print(f"\n✅ SUCCESS: Alert fired at {breakout_alert.price:.2f} - Perfect timing!")
            print(f"   This is the EXACT moment of breakout above 100")
            return True
        else:
            print(f"\n❌ FAILED: Alert fired at {breakout_alert.price:.2f} - Wrong timing!")
            print(f"   Should fire around 101 (breakout), not at column end")
            return False
    else:
        print(f"\n❌ FAILED: No BUY alert found")
        return False

def test_multiple_breakouts():
    """Test that only the FIRST breakout triggers alert, not subsequent ones."""
    print("\n🎯 Testing Multiple Breakouts (Only First Should Alert)")
    print("=" * 60)
    
    # Create scenario with multiple breakouts: 100->105->110->115
    # Only first breakout above 100 should trigger alert
    highs = [95, 96, 97, 98, 99, 100,  # First peak at 100
             99, 98, 97,                # Small pullback
             98, 99, 100, 101, 102, 103, 104, 105,  # First breakout to 105
             104, 103, 102,             # Pullback
             103, 104, 105, 106, 107, 108, 109, 110,  # Second breakout to 110
             109, 108,                  # Pullback
             109, 110, 111, 112, 113, 114, 115]      # Third breakout to 115
    
    lows = [h - 1 for h in highs]  # Simple lows
    
    box_pct = 0.01
    reversal = 3
    
    # Calculate P&F points
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_pct, reversal)
    
    # Test pattern detection
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols)
    
    print(f"📊 Chart has multiple potential breakouts")
    print(f"🚨 Alerts Generated: {len(alerts)}")
    
    buy_alerts = [a for a in alerts if a.alert_type == AlertType.BUY]
    
    for alert in buy_alerts:
        print(f"  Alert at {alert.price:.2f}: {alert.trigger_reason}")
    
    # Should only have ONE buy alert (first breakout)
    if len(buy_alerts) == 1:
        print(f"\n✅ SUCCESS: Only 1 BUY alert (first breakout) - Correct!")
        return True
    else:
        print(f"\n❌ FAILED: {len(buy_alerts)} BUY alerts - Should be only 1!")
        return False

def test_o_column_breakdown():
    """Test O column breakdown timing."""
    print("\n🎯 Testing O Column Breakdown Timing")
    print("=" * 60)
    
    # Create scenario: O column from 100 down to 95, then breaks to 94
    highs = [105, 104, 103, 102, 101, 100,  # X column down to 100
             99, 98, 97, 96, 95,             # O column to 95 (previous low)
             94, 93, 92, 91, 90]             # Breakdown below 95
    
    lows = [h - 1 for h in highs]
    
    box_pct = 0.01
    reversal = 3
    
    # Calculate P&F points
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_pct, reversal)
    
    # Test pattern detection
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols)
    
    print(f"🚨 Alerts Generated: {len(alerts)}")
    
    sell_alerts = [a for a in alerts if a.alert_type == AlertType.SELL]
    
    for alert in sell_alerts:
        print(f"  SELL Alert at {alert.price:.2f}: {alert.trigger_reason}")
    
    # Check if breakdown alert fired at right moment
    if sell_alerts:
        breakdown_alert = sell_alerts[0]
        if 93 <= breakdown_alert.price <= 95:
            print(f"\n✅ SUCCESS: Breakdown alert at {breakdown_alert.price:.2f} - Good timing!")
            return True
        else:
            print(f"\n❌ FAILED: Breakdown alert at {breakdown_alert.price:.2f} - Wrong timing!")
            return False
    else:
        print(f"\n❌ FAILED: No SELL alert found")
        return False

def main():
    """Run all exact timing tests."""
    print("🎯 EXACT BREAKOUT TIMING VALIDATION")
    print("Testing: Alert at breakout moment (101), not column end (109)")
    print("=" * 70)
    
    test1 = test_exact_breakout_scenario()
    test2 = test_multiple_breakouts()
    test3 = test_o_column_breakdown()
    
    print("\n" + "=" * 70)
    print("📋 EXACT TIMING TEST RESULTS:")
    print(f"  Exact Breakout Timing: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"  Single Alert Only: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"  O Column Breakdown: {'✅ PASS' if test3 else '❌ FAIL'}")
    
    if all([test1, test2, test3]):
        print("\n🎉 ALL TESTS PASSED!")
        print("💰 Alerts fire at EXACT breakout moment - Perfect for trading!")
        print("🎯 Alert at 101 (breakout), not 109 (column end)")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("⚠️  Alert timing needs adjustment")

if __name__ == "__main__":
    main()
