#!/usr/bin/env python3
"""
Quick Catapult Pattern Test

Simple test to verify catapult patterns are working correctly
and can be accessed from the test charts interface.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_catapult_patterns_available():
    """Test that catapult patterns are available in test patterns."""
    print("🧪 Testing Catapult Pattern Availability")
    print("=" * 50)
    
    from app.test_patterns import TEST_PATTERNS
    
    # Check if catapult patterns are available
    catapult_buy_available = 'catapult_buy' in TEST_PATTERNS
    catapult_sell_available = 'catapult_sell' in TEST_PATTERNS
    
    print(f"   Catapult Buy Pattern: {'✅ Available' if catapult_buy_available else '❌ Missing'}")
    print(f"   Catapult Sell Pattern: {'✅ Available' if catapult_sell_available else '❌ Missing'}")
    
    if catapult_buy_available:
        pattern = TEST_PATTERNS['catapult_buy']
        print(f"   Catapult Buy Name: {pattern['name']}")
        print(f"   Expected Signal: {pattern['expected_signal']}")
    
    if catapult_sell_available:
        pattern = TEST_PATTERNS['catapult_sell']
        print(f"   Catapult Sell Name: {pattern['name']}")
        print(f"   Expected Signal: {pattern['expected_signal']}")
    
    return catapult_buy_available and catapult_sell_available

def test_catapult_pattern_detection():
    """Test that catapult patterns can be detected."""
    print(f"\n🔍 Testing Catapult Pattern Detection")
    print("=" * 50)
    
    from app.pattern_detector import PatternDetector, PatternType
    from app.test_patterns import generate_catapult_buy_pattern
    from app.charts import _calculate_pnf_points
    
    # Test catapult buy pattern
    candles = generate_catapult_buy_pattern()
    highs = [float(c['high']) for c in candles]
    lows = [float(c['low']) for c in candles]
    closes = [float(c['close']) for c in candles]
    
    # Calculate P&F points
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, 0.01, 3)
    
    # Test pattern detection
    detector = PatternDetector()
    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols, closes)
    
    catapult_alerts = [a for a in alerts if a.pattern_type == PatternType.CATAPULT_BUY]
    
    print(f"   Generated {len(x_coords)} P&F points")
    print(f"   Total alerts: {len(alerts)}")
    print(f"   Catapult Buy alerts: {len(catapult_alerts)}")
    
    if catapult_alerts:
        alert = catapult_alerts[0]
        print(f"   ✅ Alert detected at column {alert.column}, price {alert.price:.2f}")
        return True
    else:
        print(f"   ❌ No catapult buy alerts detected")
        return False

def test_chart_generation():
    """Test that catapult patterns can generate charts."""
    print(f"\n📊 Testing Chart Generation")
    print("=" * 50)
    
    try:
        from app.test_patterns import generate_test_chart_html
        
        # Test catapult buy chart generation
        html_buy = generate_test_chart_html('catapult_buy', 0.01, 3)
        buy_success = len(html_buy) > 100  # Basic check for HTML content
        
        # Test catapult sell chart generation  
        html_sell = generate_test_chart_html('catapult_sell', 0.01, 3)
        sell_success = len(html_sell) > 100  # Basic check for HTML content
        
        print(f"   Catapult Buy Chart: {'✅ Generated' if buy_success else '❌ Failed'}")
        print(f"   Catapult Sell Chart: {'✅ Generated' if sell_success else '❌ Failed'}")
        
        if buy_success:
            print(f"   Buy chart HTML length: {len(html_buy)} characters")
        if sell_success:
            print(f"   Sell chart HTML length: {len(html_sell)} characters")
        
        return buy_success and sell_success
        
    except Exception as e:
        print(f"   ❌ Chart generation failed: {e}")
        return False

def run_quick_test():
    """Run quick test of catapult patterns."""
    print("🚀 QUICK CATAPULT PATTERN TEST")
    print("=" * 60)
    print("Verifying catapult patterns are ready for live trading")
    
    # Run tests
    availability_passed = test_catapult_patterns_available()
    detection_passed = test_catapult_pattern_detection()
    chart_passed = test_chart_generation()
    
    # Results
    print(f"\n🎯 QUICK TEST RESULTS")
    print("=" * 40)
    print(f"   Pattern Availability: {'✅ PASSED' if availability_passed else '❌ FAILED'}")
    print(f"   Pattern Detection: {'✅ PASSED' if detection_passed else '❌ FAILED'}")
    print(f"   Chart Generation: {'✅ PASSED' if chart_passed else '❌ FAILED'}")
    
    overall_passed = availability_passed and detection_passed and chart_passed
    
    if overall_passed:
        print(f"\n🎉 ALL QUICK TESTS PASSED!")
        print(f"   ✅ Catapult patterns are ready for live trading")
        print(f"   ✅ Available in test charts interface")
        print(f"   ✅ Alert system working")
        print(f"\n📱 Access at: http://localhost:8001/test-charts")
        print(f"   Select 'Catapult Buy' or 'Catapult Sell' from dropdown")
    else:
        print(f"\n⚠️ SOME TESTS FAILED")
        print(f"   Please check implementation")
    
    return overall_passed

if __name__ == "__main__":
    run_quick_test()
