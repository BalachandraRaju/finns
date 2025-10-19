#!/usr/bin/env python3
"""
Test the improved catapult patterns based on user's image specifications.
"""

import sys
import os
sys.path.append('/Users/balachandra.raju/projects/finns')

from app.test_patterns import (
    generate_catapult_buy_pattern, 
    generate_catapult_sell_pattern
)
from app.charts import _calculate_pnf_points
from app.pattern_detector import PatternDetector, PatternType

def test_catapult_pattern(pattern_name, pattern_generator, expected_pattern_type, expected_alert_type):
    """Test a specific catapult pattern."""
    print(f"\n🎯 Testing {pattern_name}")
    print("=" * 60)
    
    try:
        # Generate test data
        candles = pattern_generator()
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        closes = [c['close'] for c in candles]
        
        print(f"📊 Generated {len(candles)} candles")
        print(f"📊 Price range: {min(lows):.2f} - {max(highs):.2f}")
        
        # Calculate P&F points
        x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, 0.01, 3)
        print(f"📊 Generated {len(x_coords)} P&F points")
        
        # Show P&F structure
        print(f"\n📈 P&F Pattern Structure:")
        columns = {}
        for i in range(len(x_coords)):
            col = x_coords[i]
            if col not in columns:
                columns[col] = []
            columns[col].append((y_coords[i], pnf_symbols[i]))
        
        for col in sorted(columns.keys()):
            symbols = [s for _, s in columns[col]]
            prices = [p for p, _ in columns[col]]
            symbol_type = symbols[0]
            print(f"   Column {col}: {symbol_type} column, {len(symbols)} points, range {min(prices):.0f}-{max(prices):.0f}")
        
        # Test pattern detection
        detector = PatternDetector()
        alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols, closes)
        
        print(f"\n🚨 Alert Analysis:")
        print(f"   Total alerts: {len(alerts)}")
        
        # Check for specific pattern alerts
        specific_alerts = [a for a in alerts if a.pattern_type == expected_pattern_type]
        print(f"   {pattern_name} alerts: {len(specific_alerts)}")
        
        # Show all alerts with details
        for i, alert in enumerate(alerts):
            alert_symbol = "🎯" if alert.pattern_type == expected_pattern_type else "📊"
            print(f"   {alert_symbol} Alert {i+1}: {alert.alert_type.value} - {alert.pattern_type.value}")
            print(f"      Price: {alert.price:.2f}, Column: {alert.column}")
            if hasattr(alert, 'trigger_reason'):
                print(f"      Reason: {alert.trigger_reason[:100]}...")
        
        # Verify expected alert
        if len(specific_alerts) > 0:
            alert = specific_alerts[0]
            if alert.alert_type.value == expected_alert_type:
                print(f"\n✅ SUCCESS: {pattern_name} generates correct {expected_alert_type} alert!")
                print(f"   Alert triggered at price {alert.price:.2f} on column {alert.column}")
                return True
            else:
                print(f"\n❌ WRONG SIGNAL: Expected {expected_alert_type}, got {alert.alert_type.value}")
                return False
        else:
            print(f"\n❌ NO ALERT: {pattern_name} did not generate expected alert")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run comprehensive catapult pattern tests."""
    print("🎯 IMPROVED CATAPULT PATTERN TEST")
    print("Based on user's image specifications")
    print("=" * 80)
    
    results = {}
    
    # Test catapult patterns
    patterns = [
        ("Catapult Buy (Triple Bottom + Double Bottom → X Breakout)", 
         generate_catapult_buy_pattern, PatternType.CATAPULT_BUY, "BUY"),
        ("Catapult Sell (Triple Top + Double Top → O Breakdown)", 
         generate_catapult_sell_pattern, PatternType.CATAPULT_SELL, "SELL"),
    ]
    
    for pattern_name, generator, pattern_type, expected_signal in patterns:
        results[pattern_name] = test_catapult_pattern(pattern_name, generator, pattern_type, expected_signal)
    
    # Summary
    print(f"\n📋 FINAL RESULTS SUMMARY")
    print("=" * 80)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for pattern_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {pattern_name}")
    
    print(f"\n🎯 OVERALL RESULT: {passed_tests}/{total_tests} catapult patterns working correctly")
    
    if passed_tests == total_tests:
        print("🎉 ALL CATAPULT PATTERNS ARE WORKING PERFECTLY!")
        print("🚀 Ready for live trading with accurate catapult detection!")
    else:
        print("⚠️  Some catapult patterns need further adjustment")
        print("💡 Check the pattern structure and detection logic")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    main()
