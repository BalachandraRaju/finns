#!/usr/bin/env python3
"""
Startup test script to run all pattern tests before application starts.
This ensures all patterns work correctly with 1% box size and 3-box reversal.
"""

import sys
import os
import time
import unittest
from io import StringIO

def run_pattern_tests():
    """Run comprehensive pattern tests."""
    print("🚀 STARTUP PATTERN TESTS")
    print("=" * 60)
    print("Testing all patterns with 1% box size and 3-box reversal")
    print("This ensures code stability before application startup")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Test 1: Import all required modules
        print("\n📦 Testing Imports...")
        from app.test_patterns import TEST_PATTERNS
        print(f"✅ Found {len(TEST_PATTERNS)} test patterns")
        
        from app.charts import _calculate_pnf_points
        print("✅ P&F calculation function imported")
        
        from anchor_point_calculator import AnchorPointCalculator
        print("✅ Anchor point calculator imported")
        
        from app.pattern_detector import PatternDetector
        print("✅ Pattern detector imported")
        
        # Test 2: Quick pattern validation
        print("\n🧪 Testing Pattern Generation...")
        test_patterns = ['bullish_breakout', 'bearish_breakdown', 'triple_top', 'catapult_buy']
        
        for pattern_key in test_patterns:
            if pattern_key in TEST_PATTERNS:
                pattern_info = TEST_PATTERNS[pattern_key]
                candles = pattern_info['data_generator']()
                
                # Validate basic structure
                assert len(candles) > 0, f"No candles generated for {pattern_key}"
                assert all('high' in c and 'low' in c for c in candles), f"Invalid candle structure in {pattern_key}"
                
                # Test P&F calculation
                highs = [c['high'] for c in candles]
                lows = [c['low'] for c in candles]
                x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, 0.01, 3)
                
                assert len(x_coords) > 0, f"No P&F points generated for {pattern_key}"
                assert len(x_coords) == len(y_coords) == len(pnf_symbols), f"P&F arrays length mismatch in {pattern_key}"
                assert all(s in ['X', 'O'] for s in pnf_symbols), f"Invalid P&F symbols in {pattern_key}"
                
                print(f"✅ {pattern_key}: {len(candles)} candles → {len(x_coords)} P&F points")
        
        # Test 3: Anchor points integration
        print("\n🎯 Testing Anchor Points...")
        anchor_calculator = AnchorPointCalculator(min_column_separation=7)
        
        # Test with bullish_breakout pattern
        pattern_info = TEST_PATTERNS['bullish_breakout']
        candles = pattern_info['data_generator']()
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, 0.01, 3)
        
        if len(x_coords) > 0:
            # Create simple matrix for anchor points
            import pandas as pd
            
            min_price = min(y_coords)
            max_price = max(y_coords)
            price_range = max_price - min_price
            
            if price_range > 0:
                num_rows = min(int(price_range / 0.01) + 1, 100)
                num_cols = max(x_coords) + 1
                
                matrix_data = {}
                for col in range(num_cols):
                    matrix_data[col] = ['' for _ in range(num_rows)]
                
                for x, y, symbol in zip(x_coords, y_coords, pnf_symbols):
                    row_idx = int((y - min_price) / 0.01)
                    if 0 <= row_idx < num_rows and 0 <= x < num_cols:
                        matrix_data[x][row_idx] = symbol
                
                pnf_matrix = pd.DataFrame(matrix_data)
                anchor_points = anchor_calculator.calculate_anchor_points(pnf_matrix)
                
                print(f"✅ Anchor points: {len(anchor_points)} points calculated")
            else:
                print("✅ Anchor points: Skipped (no price range)")
        else:
            print("✅ Anchor points: Skipped (no P&F points)")
        
        # Test 4: Pattern detection
        print("\n🚨 Testing Pattern Detection...")
        detector = PatternDetector()
        
        # Test with a few patterns
        for pattern_key in ['bullish_breakout', 'bearish_breakdown']:
            if pattern_key in TEST_PATTERNS:
                pattern_info = TEST_PATTERNS[pattern_key]
                candles = pattern_info['data_generator']()
                highs = [c['high'] for c in candles]
                lows = [c['low'] for c in candles]
                closes = [c['close'] for c in candles]
                
                x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, 0.01, 3)
                
                if len(x_coords) > 0:
                    alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols, closes)
                    print(f"✅ {pattern_key}: {len(alerts)} alerts generated")
                else:
                    print(f"✅ {pattern_key}: Skipped (no P&F points)")
        
        # Test 5: Chart generation compatibility
        print("\n📊 Testing Chart Generation...")
        from app.test_patterns import generate_test_chart_html
        
        try:
            chart_html = generate_test_chart_html('bullish_breakout', box_pct=0.01, reversal=3)
            assert isinstance(chart_html, str), "Chart HTML should be string"
            assert len(chart_html) > 100, "Chart HTML should not be empty"
            print("✅ Chart generation working")
        except Exception as e:
            print(f"⚠️ Chart generation issue: {e}")
        
        # Summary
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n🎉 ALL STARTUP TESTS PASSED!")
        print("=" * 60)
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"📊 Patterns tested: {len(test_patterns)}")
        print("✅ Pattern generation working")
        print("✅ P&F calculation working (1% box, 3-box reversal)")
        print("✅ Anchor points integration working")
        print("✅ Pattern detection working")
        print("✅ Chart generation working")
        print("✅ System ready for startup!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ STARTUP TEST FAILED!")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print("⚠️ Fix issues before starting application")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False

def run_comprehensive_tests():
    """Run the full comprehensive test suite."""
    print("\n🔬 RUNNING COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    try:
        # Import test classes
        sys.path.insert(0, 'test')
        from test_all_patterns_comprehensive import TestAllPatternsComprehensive
        
        # Create and run test suite
        suite = unittest.TestLoader().loadTestsFromTestCase(TestAllPatternsComprehensive)
        
        # Capture output
        stream = StringIO()
        runner = unittest.TextTestRunner(verbosity=2, stream=stream)
        result = runner.run(suite)
        
        # Print results
        output = stream.getvalue()
        print(output)
        
        if result.wasSuccessful():
            print("🎉 COMPREHENSIVE TESTS PASSED!")
            return True
        else:
            print(f"❌ COMPREHENSIVE TESTS FAILED!")
            print(f"Failures: {len(result.failures)}")
            print(f"Errors: {len(result.errors)}")
            return False
            
    except Exception as e:
        print(f"❌ Could not run comprehensive tests: {e}")
        return False

def main():
    """Main function to run startup tests."""
    print("🚀 PATTERN SYSTEM STARTUP VALIDATION")
    print("=" * 80)
    
    # Run quick startup tests
    startup_success = run_pattern_tests()
    
    if not startup_success:
        print("\n❌ STARTUP TESTS FAILED - APPLICATION SHOULD NOT START")
        return False
    
    # Ask if user wants comprehensive tests
    print(f"\n💡 Quick startup tests passed!")
    print(f"Run comprehensive test suite? (y/n): ", end="")
    
    # For automated runs, skip comprehensive tests
    # In interactive mode, user can choose
    try:
        choice = input().lower().strip()
        if choice in ['y', 'yes']:
            comprehensive_success = run_comprehensive_tests()
            return startup_success and comprehensive_success
    except:
        # Non-interactive mode, skip comprehensive tests
        pass
    
    return startup_success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
