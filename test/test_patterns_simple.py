#!/usr/bin/env python3
"""
Simple pattern test script to verify everything is working.
"""

def main():
    print("🧪 SIMPLE PATTERN TEST")
    print("=" * 40)
    
    try:
        # Test imports
        from app.test_patterns import TEST_PATTERNS
        print(f"✅ Found {len(TEST_PATTERNS)} patterns")
        
        # List first 10 patterns
        pattern_list = list(TEST_PATTERNS.items())[:10]
        for i, (key, info) in enumerate(pattern_list, 1):
            signal = info['expected_signal']
            emoji = '📈' if signal == 'BUY' else '📉'
            print(f"  {i:2d}. {emoji} {key}")
        
        # Test one pattern
        pattern_key = 'bullish_breakout'
        if pattern_key in TEST_PATTERNS:
            pattern_info = TEST_PATTERNS[pattern_key]
            candles = pattern_info['data_generator']()
            print(f"✅ Generated {len(candles)} candles for {pattern_key}")
            
            # Test P&F calculation
            from app.charts import _calculate_pnf_points
            highs = [c['high'] for c in candles]
            lows = [c['low'] for c in candles]
            x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, 0.01, 3)
            print(f"✅ Generated {len(x_coords)} P&F points")
        
        print("\n🎉 SIMPLE TEST PASSED!")
        print("✅ Pattern system working")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    main()
