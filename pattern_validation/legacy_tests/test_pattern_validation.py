#!/usr/bin/env python3
"""
Test script to validate that the test patterns are working correctly.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.test_patterns import TEST_PATTERNS, generate_test_chart_html

def test_all_patterns():
    """Test all patterns to ensure they generate charts correctly."""
    print("🧪 Testing Chart Pattern Generation")
    print("=" * 50)
    
    for pattern_name, pattern_info in TEST_PATTERNS.items():
        print(f"\n📊 Testing: {pattern_info['name']}")
        print(f"   Expected Signal: {pattern_info['expected_signal']}")
        print(f"   Description: {pattern_info['description']}")
        
        try:
            # Generate test data
            candles = pattern_info['data_generator']()
            print(f"   ✅ Generated {len(candles)} candles")
            
            # Test chart generation
            chart_html = generate_test_chart_html(pattern_name, box_pct=0.01, reversal=3)
            
            if chart_html and len(chart_html) > 100:  # Basic check for valid HTML
                print(f"   ✅ Chart HTML generated successfully ({len(chart_html)} chars)")
            else:
                print(f"   ❌ Chart HTML generation failed")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print("   - All patterns should generate valid chart HTML")
    print("   - Charts should display the expected patterns")
    print("   - Signals should match the expected directions")
    print("\n📝 Next Steps:")
    print("   1. Start the application: uvicorn app.main:app --reload")
    print("   2. Visit: http://localhost:8000/test-charts")
    print("   3. Test each pattern visually")
    print("   4. Verify signals match expectations")

def test_single_pattern(pattern_name):
    """Test a single pattern in detail."""
    if pattern_name not in TEST_PATTERNS:
        print(f"❌ Pattern '{pattern_name}' not found")
        print(f"Available patterns: {list(TEST_PATTERNS.keys())}")
        return
    
    pattern_info = TEST_PATTERNS[pattern_name]
    print(f"🔍 Detailed Test: {pattern_info['name']}")
    print("=" * 50)
    
    # Generate data
    candles = pattern_info['data_generator']()
    print(f"📊 Generated {len(candles)} candles")
    
    # Show price data
    print("\n💰 Price Data:")
    for i, candle in enumerate(candles):
        print(f"   Day {i+1:2d}: O:{candle['open']:6.1f} H:{candle['high']:6.1f} L:{candle['low']:6.1f} C:{candle['close']:6.1f}")
    
    # Test different box sizes
    print(f"\n📈 Testing different box sizes:")
    for box_pct in [0.005, 0.01, 0.02]:
        try:
            chart_html = generate_test_chart_html(pattern_name, box_pct=box_pct, reversal=3)
            status = "✅" if chart_html and len(chart_html) > 100 else "❌"
            print(f"   {status} Box Size {box_pct*100:4.1f}%: {len(chart_html) if chart_html else 0} chars")
        except Exception as e:
            print(f"   ❌ Box Size {box_pct*100:4.1f}%: Error - {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test specific pattern
        pattern_name = sys.argv[1]
        test_single_pattern(pattern_name)
    else:
        # Test all patterns
        test_all_patterns()
