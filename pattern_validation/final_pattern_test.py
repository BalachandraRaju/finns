#!/usr/bin/env python3
"""
Final comprehensive test of all fixed patterns.
"""

import sys
import os
sys.path.append('/Users/balachandra.raju/projects/finns')

from app.test_patterns import (
    generate_catapult_buy_pattern, 
    generate_catapult_sell_pattern,
    generate_pole_follow_through_buy_pattern,
    generate_pole_follow_through_sell_pattern
)
from app.charts import _calculate_pnf_points
from app.pattern_detector import PatternDetector, PatternType

def test_pattern(pattern_name, pattern_generator, expected_pattern_type, expected_alert_type):
    """Test a specific pattern."""
    print(f"\n🧪 Testing {pattern_name}")
    print("-" * 50)
    
    try:
        # Generate test data
        candles = pattern_generator()
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        closes = [c['close'] for c in candles]
        
        print(f"📊 Generated {len(candles)} candles")
        print(f"📊 Price range: {min(lows):.2f} - {max(highs):.2f}")
        print(f"📊 Data types: {type(highs[0])}, {type(lows[0])}")
        
        # Calculate P&F points
        x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, 0.01, 3)
        print(f"📊 Generated {len(x_coords)} P&F points")
        
        # Test pattern detection
        detector = PatternDetector()
        alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols, closes)
        
        print(f"🚨 Total alerts: {len(alerts)}")
        
        # Check for specific pattern alerts
        specific_alerts = [a for a in alerts if a.pattern_type == expected_pattern_type]
        print(f"🎯 {pattern_name} alerts: {len(specific_alerts)}")
        
        # Show all alerts
        for alert in alerts:
            alert_symbol = "✅" if alert.pattern_type == expected_pattern_type else "📊"
            print(f"   {alert_symbol} {alert.alert_type.value}: {alert.pattern_type.value}")
        
        # Verify expected alert
        if len(specific_alerts) > 0:
            alert = specific_alerts[0]
            if alert.alert_type.value == expected_alert_type:
                print(f"✅ SUCCESS: {pattern_name} generates correct {expected_alert_type} alert!")
                return True
            else:
                print(f"❌ WRONG SIGNAL: Expected {expected_alert_type}, got {alert.alert_type.value}")
                return False
        else:
            print(f"❌ NO ALERT: {pattern_name} did not generate expected alert")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run comprehensive pattern tests."""
    print("🎯 FINAL COMPREHENSIVE PATTERN TEST")
    print("=" * 60)
    
    results = {}
    
    # Test all patterns
    patterns = [
        ("Catapult Buy", generate_catapult_buy_pattern, PatternType.CATAPULT_BUY, "BUY"),
        ("Catapult Sell", generate_catapult_sell_pattern, PatternType.CATAPULT_SELL, "SELL"),
        ("100% Pole Follow Through Buy", generate_pole_follow_through_buy_pattern, PatternType.POLE_FOLLOW_THROUGH_BUY, "BUY"),
        ("100% Pole Follow Through Sell", generate_pole_follow_through_sell_pattern, PatternType.POLE_FOLLOW_THROUGH_SELL, "SELL"),
    ]
    
    for pattern_name, generator, pattern_type, expected_signal in patterns:
        results[pattern_name] = test_pattern(pattern_name, generator, pattern_type, expected_signal)
    
    # Summary
    print(f"\n📋 FINAL RESULTS SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for pattern_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {pattern_name}")
    
    print(f"\n🎯 OVERALL RESULT: {passed_tests}/{total_tests} patterns working correctly")
    
    if passed_tests == total_tests:
        print("🎉 ALL PATTERNS ARE WORKING PERFECTLY!")
        print("🚀 Ready for live trading!")
    else:
        print("⚠️  Some patterns need further adjustment")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    main()
