#!/usr/bin/env python3
"""
Test script to verify alerts fire on the LATEST column for live trading.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.pattern_detector import PatternDetector, AlertType
from app.charts import _calculate_pnf_points

def test_live_breakout_alert():
    """Test that breakout alert fires on the LATEST column, not historical ones."""
    print("🚨 Testing LIVE Trading Alert Timing")
    print("=" * 60)
    
    # Simulate real trading scenario: price builds up then breaks out NOW
    highs = [100, 101, 102, 103, 102, 103, 104, 103, 104, 105, 110]  # Breakout at END
    lows =  [99,  100, 101, 102, 101, 102, 103, 102, 103, 104, 109]
    
    box_pct = 0.01
    reversal = 3
    
    # Calculate P&F points
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_pct, reversal)
    
    print(f"📊 P&F Chart Data:")
    for i, (x, y, sym) in enumerate(zip(x_coords, y_coords, pnf_symbols)):
        marker = "👈 LATEST" if i == len(x_coords) - 1 else ""
        print(f"  Column {x}: {sym} at {y:.2f} {marker}")
    
    # Test pattern detection
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols)
    
    print(f"\n🚨 LIVE Trading Alerts: {len(alerts)}")
    
    latest_column = max(x_coords)
    
    for alert in alerts:
        is_latest = "✅ LIVE ALERT" if alert.column == latest_column else "❌ OLD ALERT"
        print(f"  Column {alert.column}: {alert.alert_type.value} - {is_latest}")
        print(f"    Reason: {alert.trigger_reason}")
    
    # Verify alerts are on latest column
    latest_alerts = [a for a in alerts if a.column == latest_column]
    old_alerts = [a for a in alerts if a.column != latest_column]
    
    print(f"\n📊 Alert Analysis:")
    print(f"  Latest Column: {latest_column}")
    print(f"  Alerts on Latest Column: {len(latest_alerts)} ✅")
    print(f"  Alerts on Old Columns: {len(old_alerts)} {'❌ BAD' if old_alerts else '✅ GOOD'}")
    
    if latest_alerts and not old_alerts:
        print(f"\n🎉 SUCCESS: Alert fired on LATEST column {latest_column} - Perfect for live trading!")
        return True
    elif old_alerts:
        print(f"\n❌ FAILED: Found alerts on old columns - Not useful for live trading!")
        return False
    else:
        print(f"\n⚠️  No alerts found - Check if breakout is significant enough")
        return False

def test_live_breakdown_alert():
    """Test that breakdown alert fires on the LATEST column."""
    print("\n🚨 Testing LIVE Breakdown Alert Timing")
    print("=" * 60)
    
    # Simulate real trading scenario: price declines then breaks down NOW
    highs = [120, 119, 118, 117, 118, 117, 116, 117, 116, 115, 110]  # Breakdown at END
    lows =  [119, 118, 117, 116, 117, 116, 115, 116, 115, 114, 109]
    
    box_pct = 0.01
    reversal = 3
    
    # Calculate P&F points
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_pct, reversal)
    
    print(f"📊 P&F Chart Data:")
    for i, (x, y, sym) in enumerate(zip(x_coords, y_coords, pnf_symbols)):
        marker = "👈 LATEST" if i == len(x_coords) - 1 else ""
        print(f"  Column {x}: {sym} at {y:.2f} {marker}")
    
    # Test pattern detection
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols)
    
    print(f"\n🚨 LIVE Trading Alerts: {len(alerts)}")
    
    latest_column = max(x_coords)
    
    for alert in alerts:
        is_latest = "✅ LIVE ALERT" if alert.column == latest_column else "❌ OLD ALERT"
        print(f"  Column {alert.column}: {alert.alert_type.value} - {is_latest}")
        print(f"    Reason: {alert.trigger_reason}")
    
    # Verify alerts are on latest column
    latest_alerts = [a for a in alerts if a.column == latest_column]
    old_alerts = [a for a in alerts if a.column != latest_column]
    
    print(f"\n📊 Alert Analysis:")
    print(f"  Latest Column: {latest_column}")
    print(f"  Alerts on Latest Column: {len(latest_alerts)} ✅")
    print(f"  Alerts on Old Columns: {len(old_alerts)} {'❌ BAD' if old_alerts else '✅ GOOD'}")
    
    if latest_alerts and not old_alerts:
        print(f"\n🎉 SUCCESS: Alert fired on LATEST column {latest_column} - Perfect for live trading!")
        return True
    elif old_alerts:
        print(f"\n❌ FAILED: Found alerts on old columns - Not useful for live trading!")
        return False
    else:
        print(f"\n⚠️  No alerts found - Check if breakdown is significant enough")
        return False

def test_incremental_data():
    """Test how alerts behave when data comes in incrementally (like real trading)."""
    print("\n🚨 Testing Incremental Data (Real Trading Simulation)")
    print("=" * 60)
    
    # Simulate data coming in one candle at a time
    base_highs = [100, 101, 102, 103, 104]
    base_lows =  [99,  100, 101, 102, 103]
    
    # Add breakout candle
    breakout_high = 108
    breakout_low = 107
    
    print("📊 Simulating incremental data arrival:")
    
    # Test with base data (no alerts expected)
    x_coords_base, y_coords_base, symbols_base = _calculate_pnf_points(base_highs, base_lows, 0.01, 3)
    detector_base = PatternDetector()
    alerts_base = detector_base.analyze_pattern_formation(x_coords_base, y_coords_base, symbols_base)
    
    print(f"  Base data: {len(alerts_base)} alerts")
    
    # Test with breakout data (alert expected on latest)
    full_highs = base_highs + [breakout_high]
    full_lows = base_lows + [breakout_low]
    
    x_coords_full, y_coords_full, symbols_full = _calculate_pnf_points(full_highs, full_lows, 0.01, 3)
    detector_full = PatternDetector()
    alerts_full = detector_full.analyze_pattern_formation(x_coords_full, y_coords_full, symbols_full)
    
    print(f"  With breakout: {len(alerts_full)} alerts")
    
    if alerts_full:
        latest_column = max(x_coords_full)
        for alert in alerts_full:
            timing = "✅ LIVE" if alert.column == latest_column else "❌ OLD"
            print(f"    Column {alert.column}: {alert.alert_type.value} - {timing}")
    
    # Check if new alert is on latest column
    if alerts_full:
        latest_column = max(x_coords_full)
        latest_alerts = [a for a in alerts_full if a.column == latest_column]
        return len(latest_alerts) > 0
    
    return False

def main():
    """Run all live trading alert tests."""
    print("🔥 LIVE TRADING ALERT VALIDATION")
    print("Critical: Alerts must fire on LATEST column for real trading!")
    print("=" * 70)
    
    test1 = test_live_breakout_alert()
    test2 = test_live_breakdown_alert()
    test3 = test_incremental_data()
    
    print("\n" + "=" * 70)
    print("📋 LIVE TRADING TEST RESULTS:")
    print(f"  Live Breakout Alert: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"  Live Breakdown Alert: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"  Incremental Data: {'✅ PASS' if test3 else '❌ FAIL'}")
    
    if all([test1, test2, test3]):
        print("\n🎉 ALL TESTS PASSED!")
        print("💰 Alerts are ready for LIVE TRADING!")
        print("🚨 Alerts fire on LATEST column - Perfect timing for real trades!")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("⚠️  Alerts are NOT ready for live trading!")
        print("🔧 Fix required: Alerts must fire on LATEST column only!")

if __name__ == "__main__":
    main()
