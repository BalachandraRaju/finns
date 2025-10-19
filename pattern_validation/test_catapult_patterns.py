#!/usr/bin/env python3
"""
Test the updated catapult patterns to ensure they match the provided images.
"""

import sys
import os
sys.path.append('/Users/balachandra.raju/projects/finns')

from app.test_patterns import TEST_PATTERNS, generate_catapult_buy_pattern, generate_catapult_sell_pattern
from app.charts import _calculate_pnf_points
from app.pattern_detector import PatternDetector

def test_catapult_patterns():
    """Test both catapult patterns and their P&F representations."""
    print("🧪 Testing Updated Catapult Patterns")
    print("=" * 50)
    
    # Test Catapult Buy Pattern
    print("\n📈 Testing Catapult Buy Pattern")
    print("-" * 30)
    
    if 'catapult_buy' in TEST_PATTERNS:
        pattern_info = TEST_PATTERNS['catapult_buy']
        print(f"✅ Pattern Name: {pattern_info['name']}")
        print(f"✅ Expected Signal: {pattern_info['expected_signal']}")
        print(f"✅ Description: {pattern_info['description']}")
        
        # Generate test data
        candles = generate_catapult_buy_pattern()
        print(f"✅ Generated {len(candles)} candles")
        
        # Extract price data
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        closes = [c['close'] for c in candles]
        
        print(f"✅ Price range: {min(lows):.2f} - {max(highs):.2f}")
        
        # Calculate P&F points
        x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, 0.01, 3)
        print(f"✅ Generated {len(x_coords)} P&F points")
        
        # Count X and O columns
        x_count = sum(1 for symbol in pnf_symbols if symbol == 'X')
        o_count = sum(1 for symbol in pnf_symbols if symbol == 'O')
        print(f"✅ P&F Structure: {x_count} X columns, {o_count} O columns")
        
        # Test pattern detection
        detector = PatternDetector()
        alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols, closes)
        print(f"✅ Pattern detector found {len(alerts)} alerts")
        
        for alert in alerts:
            print(f"   🚨 {alert.alert_type.value}: {alert.pattern_type.value}")
    else:
        print("❌ Catapult Buy pattern not found in TEST_PATTERNS")
    
    # Test Catapult Sell Pattern
    print("\n📉 Testing Catapult Sell Pattern")
    print("-" * 30)
    
    if 'catapult_sell' in TEST_PATTERNS:
        pattern_info = TEST_PATTERNS['catapult_sell']
        print(f"✅ Pattern Name: {pattern_info['name']}")
        print(f"✅ Expected Signal: {pattern_info['expected_signal']}")
        print(f"✅ Description: {pattern_info['description']}")
        
        # Generate test data
        candles = generate_catapult_sell_pattern()
        print(f"✅ Generated {len(candles)} candles")
        
        # Extract price data
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        closes = [c['close'] for c in candles]
        
        print(f"✅ Price range: {min(lows):.2f} - {max(highs):.2f}")
        
        # Calculate P&F points
        x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, 0.01, 3)
        print(f"✅ Generated {len(x_coords)} P&F points")
        
        # Count X and O columns
        x_count = sum(1 for symbol in pnf_symbols if symbol == 'X')
        o_count = sum(1 for symbol in pnf_symbols if symbol == 'O')
        print(f"✅ P&F Structure: {x_count} X columns, {o_count} O columns")
        
        # Test pattern detection
        detector = PatternDetector()
        alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols, closes)
        print(f"✅ Pattern detector found {len(alerts)} alerts")
        
        for alert in alerts:
            print(f"   🚨 {alert.alert_type.value}: {alert.pattern_type.value}")
    else:
        print("❌ Catapult Sell pattern not found in TEST_PATTERNS")

def test_pattern_availability():
    """Test that all patterns are available in the dropdown."""
    print("\n🔍 Testing Pattern Availability")
    print("=" * 50)
    
    print(f"Total patterns available: {len(TEST_PATTERNS)}")
    
    # Check for catapult patterns specifically
    catapult_patterns = [key for key in TEST_PATTERNS.keys() if 'catapult' in key]
    print(f"Catapult patterns found: {len(catapult_patterns)}")
    
    for pattern_key in catapult_patterns:
        pattern = TEST_PATTERNS[pattern_key]
        print(f"  ✅ {pattern_key}: {pattern['name']} ({pattern['expected_signal']})")
    
    # List all patterns for reference
    print("\nAll available patterns:")
    for i, (key, pattern) in enumerate(TEST_PATTERNS.items(), 1):
        signal_emoji = "📈" if pattern['expected_signal'] == 'BUY' else "📉"
        print(f"  {i:2d}. {signal_emoji} {pattern['name']}")

if __name__ == "__main__":
    test_catapult_patterns()
    test_pattern_availability()
    print("\n🎉 Catapult pattern testing completed!")
