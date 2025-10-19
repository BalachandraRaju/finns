#!/usr/bin/env python3
"""
Test script with manually created P&F data to test exact breakout timing.
Creates the exact scenario: X column to 100, O column down, X column 101->109
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.pattern_detector import PatternDetector, AlertType

def test_manual_pnf_scenario():
    """Test with manually created P&F data matching the exact scenario."""
    print("🎯 Manual P&F Test: X(100) -> O(down) -> X(101->109)")
    print("Alert should fire at 101, not 109")
    print("=" * 60)
    
    # Manually create the exact P&F scenario described
    # Column 1: X column going up to 100
    # Column 2: O column going down
    # Column 3: X column going from 101 to 109
    
    x_coords = []
    y_coords = []
    pnf_symbols = []
    
    # Column 1: X column up to 100 (5 X's)
    for i, price in enumerate([96, 97, 98, 99, 100]):
        x_coords.append(1)
        y_coords.append(price)
        pnf_symbols.append('X')
    
    # Column 2: O column down (3 O's)
    for i, price in enumerate([99, 98, 97]):
        x_coords.append(2)
        y_coords.append(price)
        pnf_symbols.append('O')
    
    # Column 3: X column from 101 to 109 (9 X's)
    # This is where alert should fire at 101 (first X above 100)
    for i, price in enumerate([98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109]):
        x_coords.append(3)
        y_coords.append(price)
        pnf_symbols.append('X')
    
    print(f"📊 Manual P&F Chart:")
    print(f"Total points: {len(x_coords)}")
    
    # Show the structure
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
        print(f"  Column {col_num}: {symbol} from {min_price:.0f} to {max_price:.0f} ({len(points)} points)")
        
        # Show key points for column 3
        if col_num == 3:
            print(f"    Key: 101 should trigger alert (breakout above 100)")
            print(f"    Key: 109 is just continuation (no new alert)")
    
    # Test pattern detection
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols)
    
    print(f"\n🚨 Alerts Generated: {len(alerts)}")
    
    for alert in alerts:
        timing_analysis = ""
        if alert.alert_type == AlertType.BUY:
            if alert.price == 101:
                timing_analysis = "✅ PERFECT - Alert at breakout moment!"
            elif alert.price > 105:
                timing_analysis = "❌ TOO LATE - Alert at column end"
            else:
                timing_analysis = "⚠️ CLOSE - Near breakout point"
        
        print(f"  Column {alert.column}: {alert.alert_type.value} at {alert.price:.0f} {timing_analysis}")
        print(f"    Reason: {alert.trigger_reason}")
    
    # Check for the perfect timing
    buy_alerts = [a for a in alerts if a.alert_type == AlertType.BUY]
    
    if buy_alerts:
        breakout_alert = buy_alerts[0]
        if breakout_alert.price == 101:
            print(f"\n🎉 PERFECT: Alert fired at {breakout_alert.price:.0f} - Exact breakout moment!")
            return True
        elif 100 < breakout_alert.price <= 103:
            print(f"\n✅ GOOD: Alert fired at {breakout_alert.price:.0f} - Close to breakout")
            return True
        else:
            print(f"\n❌ WRONG: Alert fired at {breakout_alert.price:.0f} - Should be at 101")
            return False
    else:
        print(f"\n❌ FAILED: No BUY alert found")
        return False

def test_step_by_step_processing():
    """Test step-by-step processing to see exactly when alert fires."""
    print("\n🔍 Step-by-Step Processing Analysis")
    print("=" * 60)
    
    # Create the scenario step by step
    base_x = [1, 1, 1, 1, 1, 2, 2, 2, 3, 3, 3]  # Columns
    base_y = [96, 97, 98, 99, 100, 99, 98, 97, 98, 99, 100]  # Up to 100 again
    base_s = ['X', 'X', 'X', 'X', 'X', 'O', 'O', 'O', 'X', 'X', 'X']
    
    # Add the critical points one by one
    critical_points = [101, 102, 103, 104, 105, 106, 107, 108, 109]
    
    print("📊 Processing data point by point:")
    
    for i, new_price in enumerate(critical_points):
        # Add the new point
        test_x = base_x + [3] * (i + 1)
        test_y = base_y + critical_points[:i + 1]
        test_s = base_s + ['X'] * (i + 1)
        
        # Test detection
        detector = PatternDetector()
        alerts = detector.analyze_pattern_formation(test_x, test_y, test_s)
        
        buy_alerts = [a for a in alerts if a.alert_type == AlertType.BUY]
        
        if buy_alerts and not hasattr(test_step_by_step_processing, 'alert_fired'):
            # First alert
            alert = buy_alerts[0]
            print(f"  🚨 FIRST ALERT at price {new_price}: {alert.trigger_reason}")
            test_step_by_step_processing.alert_fired = True
            
            if new_price == 101:
                print(f"     ✅ PERFECT TIMING - Alert at exact breakout!")
                return True
            else:
                print(f"     ❌ WRONG TIMING - Should be at 101")
                return False
        elif i == 0:  # First iteration, check if alert fired
            if buy_alerts:
                print(f"  🚨 Alert fired at {new_price}")
            else:
                print(f"  ⏳ No alert yet at {new_price}")
    
    print(f"  ❌ No alert fired during the sequence")
    return False

def main():
    """Run manual P&F scenario tests."""
    print("🎯 MANUAL P&F SCENARIO TESTING")
    print("Testing exact scenario: X(100) -> O(down) -> X(101->109)")
    print("=" * 70)
    
    test1 = test_manual_pnf_scenario()
    test2 = test_step_by_step_processing()
    
    print("\n" + "=" * 70)
    print("📋 MANUAL SCENARIO TEST RESULTS:")
    print(f"  Manual P&F Scenario: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"  Step-by-Step Analysis: {'✅ PASS' if test2 else '❌ FAIL'}")
    
    if test1 and test2:
        print("\n🎉 SUCCESS: Alert timing is correct!")
        print("💰 Alert fires at breakout moment (101), not column end (109)")
    else:
        print("\n❌ FAILED: Alert timing needs fixing")
        print("🔧 Alert should fire at 101 (breakout), not later")

if __name__ == "__main__":
    main()
