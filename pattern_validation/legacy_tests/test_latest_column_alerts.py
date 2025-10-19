#!/usr/bin/env python3
"""
Test script to verify alerts fire ONLY on the LATEST column, not historical ones.
Tests the scenario: Multiple X columns, alert should fire on LATEST X column only.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.pattern_detector import PatternDetector, AlertType

def test_multiple_x_columns_scenario():
    """Test multiple X columns - alert should fire on LATEST column only."""
    print("🎯 Testing Multiple X Columns - Latest Column Alert Only")
    print("Scenario: Multiple X columns, alert should fire on LATEST column")
    print("=" * 70)
    
    # Create scenario similar to the chart shown:
    # Multiple X columns with breakouts, but we only want alert on the LATEST one
    
    x_coords = []
    y_coords = []
    pnf_symbols = []
    
    # Column 1: Initial X column (100-103)
    for price in [100, 101, 102, 103]:
        x_coords.append(1)
        y_coords.append(price)
        pnf_symbols.append('X')
    
    # Column 2: O column down
    for price in [102, 101, 100]:
        x_coords.append(2)
        y_coords.append(price)
        pnf_symbols.append('O')
    
    # Column 3: X column (104-107) - This could trigger alert but shouldn't
    for price in [101, 102, 103, 104, 105, 106, 107]:
        x_coords.append(3)
        y_coords.append(price)
        pnf_symbols.append('X')
    
    # Column 4: O column down
    for price in [106, 105, 104]:
        x_coords.append(4)
        y_coords.append(price)
        pnf_symbols.append('O')
    
    # Column 5: X column (108-115) - This could trigger alert but shouldn't
    for price in [105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115]:
        x_coords.append(5)
        y_coords.append(price)
        pnf_symbols.append('X')
    
    # Column 6: O column down
    for price in [114, 113, 112]:
        x_coords.append(6)
        y_coords.append(price)
        pnf_symbols.append('O')
    
    # Column 7: LATEST X column (116-122) - Alert should fire HERE
    for price in [113, 114, 115, 116, 117, 118, 119, 120, 121, 122]:
        x_coords.append(7)
        y_coords.append(price)
        pnf_symbols.append('X')
    
    print(f"📊 Chart Structure:")
    print(f"Total points: {len(x_coords)}")
    
    # Show column structure
    columns = {}
    for i, (x, y, sym) in enumerate(zip(x_coords, y_coords, pnf_symbols)):
        if x not in columns:
            columns[x] = []
        columns[x].append((y, sym))
    
    for col_num in sorted(columns.keys()):
        points = columns[col_num]
        symbol = points[0][1]
        prices = [p[0] for p in points]
        min_price, max_price = min(prices), max(prices)
        is_latest = "👈 LATEST" if col_num == max(columns.keys()) else ""
        print(f"  Column {col_num}: {symbol} from {min_price:.0f} to {max_price:.0f} {is_latest}")
    
    # Test pattern detection
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols)
    
    print(f"\n🚨 Alerts Generated: {len(alerts)}")
    
    latest_column = max(x_coords)
    
    for alert in alerts:
        is_latest = "✅ LATEST COLUMN" if alert.column == latest_column else "❌ OLD COLUMN"
        print(f"  Column {alert.column}: {alert.alert_type.value} at {alert.price:.0f} - {is_latest}")
        print(f"    Reason: {alert.trigger_reason}")
    
    # Verify alert is ONLY on latest column
    latest_alerts = [a for a in alerts if a.column == latest_column]
    old_alerts = [a for a in alerts if a.column != latest_column]
    
    print(f"\n📊 Alert Analysis:")
    print(f"  Latest Column: {latest_column}")
    print(f"  Alerts on Latest Column: {len(latest_alerts)} {'✅' if latest_alerts else '❌'}")
    print(f"  Alerts on Old Columns: {len(old_alerts)} {'❌ BAD' if old_alerts else '✅ GOOD'}")
    
    if latest_alerts and not old_alerts:
        latest_alert = latest_alerts[0]
        if latest_alert.price >= 116:  # Should be around 116+ (breakout above 115)
            print(f"\n🎉 PERFECT: Alert on LATEST column {latest_column} at {latest_alert.price:.0f}")
            print(f"💰 This is the current breakout - perfect for live trading!")
            return True
        else:
            print(f"\n⚠️ Alert on latest column but wrong price: {latest_alert.price:.0f}")
            return False
    elif old_alerts:
        print(f"\n❌ FAILED: Found alerts on old columns - not useful for trading!")
        return False
    else:
        print(f"\n❌ FAILED: No alerts found on latest column")
        return False

def test_simple_latest_column():
    """Simple test with just 2 X columns."""
    print("\n🎯 Simple Test: 2 X Columns")
    print("=" * 50)
    
    # Simple scenario: 2 X columns, alert should be on the 2nd (latest)
    x_coords = [1, 1, 1, 2, 2, 3, 3, 3, 3, 3]  # Column 1: X, Column 2: O, Column 3: X (latest)
    y_coords = [100, 101, 102, 101, 100, 101, 102, 103, 104, 105]  # Breakout at 103 in latest column
    pnf_symbols = ['X', 'X', 'X', 'O', 'O', 'X', 'X', 'X', 'X', 'X']
    
    print(f"📊 Simple Chart: 3 columns, latest is column 3")
    print(f"  Column 1: X (100-102)")
    print(f"  Column 2: O (101-100)")
    print(f"  Column 3: X (101-105) 👈 LATEST - Alert should fire here at 103")
    
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols)
    
    print(f"\n🚨 Alerts: {len(alerts)}")
    
    latest_column = max(x_coords)
    for alert in alerts:
        is_latest = "✅ LATEST" if alert.column == latest_column else "❌ OLD"
        print(f"  Column {alert.column}: {alert.alert_type.value} at {alert.price:.0f} - {is_latest}")
    
    # Check if alert is on latest column
    latest_alerts = [a for a in alerts if a.column == latest_column]
    return len(latest_alerts) > 0 and len([a for a in alerts if a.column != latest_column]) == 0

def main():
    """Run latest column alert tests."""
    print("🚨 LATEST COLUMN ALERT VALIDATION")
    print("Critical: Alerts must fire on LATEST column only!")
    print("=" * 80)
    
    test1 = test_multiple_x_columns_scenario()
    test2 = test_simple_latest_column()
    
    print("\n" + "=" * 80)
    print("📋 LATEST COLUMN TEST RESULTS:")
    print(f"  Multiple X Columns: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"  Simple Latest Column: {'✅ PASS' if test2 else '❌ FAIL'}")
    
    if test1 and test2:
        print("\n🎉 ALL TESTS PASSED!")
        print("💰 Alerts fire ONLY on LATEST column - Perfect for live trading!")
        print("🎯 No more alerts on old columns - Clean trading signals!")
    else:
        print("\n❌ TESTS FAILED!")
        print("⚠️ Alerts are firing on old columns - Not useful for trading!")

if __name__ == "__main__":
    main()
