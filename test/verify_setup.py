#!/usr/bin/env python3
"""
Quick verification that test suite setup is working.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath('..'))

def main():
    print('🧪 QUICK TEST SUITE VERIFICATION')
    print('=' * 50)
    
    try:
        # Test imports
        from app.test_patterns import TEST_PATTERNS
        print(f'✅ Found {len(TEST_PATTERNS)} test patterns')
        
        from app.charts import _calculate_pnf_points
        print('✅ P&F calculation function available')
        
        from anchor_point_calculator import AnchorPointCalculator
        print('✅ Anchor point calculator available')
        
        # Test one pattern
        pattern_key = 'bullish_breakout'
        if pattern_key in TEST_PATTERNS:
            pattern_info = TEST_PATTERNS[pattern_key]
            candles = pattern_info['data_generator']()
            print(f'✅ Generated {len(candles)} candles for {pattern_key}')
            
            # Test P&F calculation
            highs = [c['high'] for c in candles]
            lows = [c['low'] for c in candles]
            x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, 0.01, 3)
            print(f'✅ Generated {len(x_coords)} P&F points')
        
        # List available patterns
        print(f'\n📊 Available patterns:')
        for i, (key, info) in enumerate(list(TEST_PATTERNS.items())[:10], 1):
            signal = info['expected_signal']
            emoji = '📈' if signal == 'BUY' else '📉'
            print(f'   {i:2d}. {emoji} {key}: {info["name"]}')
        
        if len(TEST_PATTERNS) > 10:
            print(f'   ... and {len(TEST_PATTERNS) - 10} more patterns')
        
        print('\n🎉 TEST SUITE SETUP WORKING!')
        print('✅ Ready to run comprehensive tests')
        return True
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
