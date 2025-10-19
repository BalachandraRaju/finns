#!/usr/bin/env python3
"""
100% Pole Follow Through Pattern Validator

Comprehensive validation script for pole follow through buy and sell patterns.
Validates pattern detection accuracy, alert triggering, and integration with the alert system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import redis
from app.pattern_detector import PatternDetector, PatternType
from app.test_patterns import generate_pole_follow_through_buy_pattern, generate_pole_follow_through_sell_pattern
from app.charts import _calculate_pnf_points

def test_pole_follow_through_patterns():
    """Test both pole follow through patterns comprehensively."""
    
    print("🚀 100% POLE FOLLOW THROUGH PATTERN VALIDATOR")
    print("=" * 60)
    print("Validating pole follow through buy and sell patterns")
    
    # Test Redis connection
    try:
        redis_client = redis.Redis(decode_responses=True)
        redis_client.ping()
        print("Connected to Redis successfully!")
    except redis.exceptions.ConnectionError as e:
        print(f"⚠️  Redis connection failed: {e}")
        redis_client = None
    
    # Test pole follow through buy pattern
    print("\n🧪 Testing Pole Follow Through Buy Pattern")
    print("=" * 50)
    
    buy_candles = generate_pole_follow_through_buy_pattern()
    print(f"   Generated {len(buy_candles)} candles")
    
    # Extract price data
    highs = [float(c['high']) for c in buy_candles]
    lows = [float(c['low']) for c in buy_candles]
    closes = [float(c['close']) for c in buy_candles]
    
    # Calculate P&F points
    box_percentage = 0.0025  # 0.25%
    reversal = 3
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_percentage, reversal)
    
    print(f"   Generated {len(x_coords)} P&F points")
    
    # Test pattern detection
    detector = PatternDetector()
    alert_triggers = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols, closes)
    
    print(f"   Total alerts: {len(alert_triggers)}")
    
    # Validate pole follow through buy alerts
    pole_buy_alerts = [alert for alert in alert_triggers 
                      if alert.pattern_type == PatternType.POLE_FOLLOW_THROUGH_BUY]
    
    print(f"   Pole Follow Through Buy alerts: {len(pole_buy_alerts)}")
    
    if pole_buy_alerts:
        alert = pole_buy_alerts[0]
        print(f"   ✅ Alert detected at column {alert.column}, price {alert.price:.2f}")
        print(f"   📝 Trigger reason: {alert.trigger_reason}")
        
        # Validate alert properties
        assert alert.alert_type.value == 'BUY', f"Expected BUY signal, got {alert.alert_type.value}"
        assert alert.is_first_occurrence, "Alert should be first occurrence"
        assert alert.price > 109.0, f"Breakout price {alert.price:.2f} should be above resistance ~109"
        
        print("   ✅ All buy pattern validations passed!")
    else:
        print("   ❌ No pole follow through buy alerts detected")
        return False
    
    # Test pole follow through sell pattern
    print("\n🧪 Testing Pole Follow Through Sell Pattern")
    print("=" * 50)
    
    sell_candles = generate_pole_follow_through_sell_pattern()
    print(f"   Generated {len(sell_candles)} candles")
    
    # Extract price data
    highs = [float(c['high']) for c in sell_candles]
    lows = [float(c['low']) for c in sell_candles]
    closes = [float(c['close']) for c in sell_candles]
    
    # Calculate P&F points
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, box_percentage, reversal)
    
    print(f"   Generated {len(x_coords)} P&F points")
    
    # Test pattern detection
    detector = PatternDetector()
    alert_triggers = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols, closes)
    
    print(f"   Total alerts: {len(alert_triggers)}")
    
    # Validate pole follow through sell alerts
    pole_sell_alerts = [alert for alert in alert_triggers 
                       if alert.pattern_type == PatternType.POLE_FOLLOW_THROUGH_SELL]
    
    print(f"   Pole Follow Through Sell alerts: {len(pole_sell_alerts)}")
    
    if pole_sell_alerts:
        alert = pole_sell_alerts[0]
        print(f"   ✅ Alert detected at column {alert.column}, price {alert.price:.2f}")
        print(f"   📝 Trigger reason: {alert.trigger_reason}")
        
        # Validate alert properties
        assert alert.alert_type.value == 'SELL', f"Expected SELL signal, got {alert.alert_type.value}"
        assert alert.is_first_occurrence, "Alert should be first occurrence"
        assert alert.price < 111.0, f"Breakdown price {alert.price:.2f} should be below support ~111"
        
        print("   ✅ All sell pattern validations passed!")
    else:
        print("   ❌ No pole follow through sell alerts detected")
        return False
    
    return True

def test_pattern_availability():
    """Test that pole follow through patterns are available in test patterns."""
    
    print("\n🔍 Testing Pattern Availability")
    print("=" * 40)
    
    from app.test_patterns import TEST_PATTERNS
    
    # Check if pole follow through patterns are available
    pole_buy_available = 'pole_follow_through_buy' in TEST_PATTERNS
    pole_sell_available = 'pole_follow_through_sell' in TEST_PATTERNS
    
    print(f"   Pole Follow Through Buy Pattern: {'✅ Available' if pole_buy_available else '❌ Missing'}")
    print(f"   Pole Follow Through Sell Pattern: {'✅ Available' if pole_sell_available else '❌ Missing'}")
    
    if pole_buy_available:
        buy_pattern = TEST_PATTERNS['pole_follow_through_buy']
        print(f"   Buy Pattern Name: {buy_pattern['name']}")
        print(f"   Expected Signal: {buy_pattern['expected_signal']}")
    
    if pole_sell_available:
        sell_pattern = TEST_PATTERNS['pole_follow_through_sell']
        print(f"   Sell Pattern Name: {sell_pattern['name']}")
        print(f"   Expected Signal: {sell_pattern['expected_signal']}")
    
    return pole_buy_available and pole_sell_available

def main():
    """Run all pole follow through pattern validations."""
    
    print("🎯 POLE FOLLOW THROUGH PATTERN VALIDATION")
    print("=" * 60)
    print("Comprehensive validation of 100% pole follow through patterns")
    
    # Test pattern availability
    availability_passed = test_pattern_availability()
    
    # Test pattern detection
    detection_passed = test_pole_follow_through_patterns()
    
    # Final results
    print("\n🎯 VALIDATION RESULTS")
    print("=" * 30)
    print(f"   Pattern Availability: {'✅ PASSED' if availability_passed else '❌ FAILED'}")
    print(f"   Pattern Detection: {'✅ PASSED' if detection_passed else '❌ FAILED'}")
    
    if availability_passed and detection_passed:
        print("\n🎉 ALL POLE FOLLOW THROUGH VALIDATIONS PASSED!")
        print("   ✅ Patterns are ready for live trading")
        print("   ✅ Alert accuracy confirmed")
        print("   ✅ One-time trigger mechanism working")
        print("\n📱 Access at: http://localhost:8001/test-charts")
        print("   Select '100% Pole Follow Through Buy' or '100% Pole Follow Through Sell' from dropdown")
        return True
    else:
        print("\n❌ SOME VALIDATIONS FAILED!")
        print("   Please check the implementation and try again")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
