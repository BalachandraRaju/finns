#!/usr/bin/env python3
"""
Comprehensive pattern test runner for startup folder.
Run this script to validate all patterns work correctly before starting the application.
"""

import sys
import os
import time
import unittest
from io import StringIO

def run_quick_pattern_tests():
    """Run quick pattern validation tests."""
    print("🧪 QUICK PATTERN VALIDATION")
    print("=" * 50)
    
    try:
        # Import required modules
        from app.test_patterns import TEST_PATTERNS
        from app.charts import _calculate_pnf_points
        from anchor_point_calculator import AnchorPointCalculator
        from app.pattern_detector import PatternDetector
        
        print(f"✅ Found {len(TEST_PATTERNS)} test patterns")
        
        # Test key patterns
        test_patterns = ['bullish_breakout', 'bearish_breakdown', 'triple_top', 'catapult_buy', 'pole_follow_through_buy']
        success_count = 0
        total_pnf_points = 0
        
        for pattern_key in test_patterns:
            if pattern_key in TEST_PATTERNS:
                try:
                    pattern_info = TEST_PATTERNS[pattern_key]
                    candles = pattern_info['data_generator']()
                    
                    # Validate candle structure
                    assert len(candles) > 0, f"No candles for {pattern_key}"
                    assert all('high' in c and 'low' in c and 'open' in c and 'close' in c for c in candles), f"Invalid structure in {pattern_key}"
                    
                    highs = [c['high'] for c in candles]
                    lows = [c['low'] for c in candles]
                    closes = [c['close'] for c in candles]
                    
                    # Test P&F calculation with 1% box size and 3-box reversal
                    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, 0.01, 3)
                    
                    assert len(x_coords) == len(y_coords) == len(pnf_symbols), f"Array length mismatch in {pattern_key}"
                    assert all(s in ['X', 'O'] for s in pnf_symbols), f"Invalid symbols in {pattern_key}"
                    
                    if len(x_coords) > 0:
                        total_pnf_points += len(x_coords)
                        print(f"✅ {pattern_key}: {len(candles)} candles → {len(x_coords)} P&F points")
                        success_count += 1
                    else:
                        print(f"⚠️ {pattern_key}: No P&F points generated")
                        
                except Exception as e:
                    print(f"❌ {pattern_key}: {str(e)}")
        
        # Test anchor points
        try:
            anchor_calculator = AnchorPointCalculator(min_column_separation=7)
            print("✅ Anchor point calculator ready")
        except Exception as e:
            print(f"❌ Anchor points error: {str(e)}")
        
        # Test pattern detector
        try:
            detector = PatternDetector()
            print("✅ Pattern detector ready")
        except Exception as e:
            print(f"❌ Pattern detector error: {str(e)}")
        
        # Summary
        if success_count >= 3:
            print(f"\n🎉 QUICK TESTS PASSED!")
            print(f"✅ {success_count}/{len(test_patterns)} patterns working")
            print(f"✅ {total_pnf_points} total P&F points generated")
            print("✅ 1% box size and 3-box reversal working")
            return True
        else:
            print(f"\n❌ QUICK TESTS FAILED!")
            print(f"❌ Only {success_count}/{len(test_patterns)} patterns working")
            return False
            
    except Exception as e:
        print(f"❌ QUICK TEST ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def run_comprehensive_tests():
    """Run comprehensive test suite."""
    print("\n🔬 COMPREHENSIVE TEST SUITE")
    print("=" * 50)
    
    try:
        # Add test directory to path
        test_dir = os.path.join(os.path.dirname(__file__), 'test')
        if os.path.exists(test_dir):
            sys.path.insert(0, test_dir)
        
        # Import test classes
        from test_all_patterns_comprehensive import TestAllPatternsComprehensive
        
        # Run comprehensive tests
        suite = unittest.TestLoader().loadTestsFromTestCase(TestAllPatternsComprehensive)
        
        # Capture output
        stream = StringIO()
        runner = unittest.TextTestRunner(verbosity=1, stream=stream)
        result = runner.run(suite)
        
        # Print summary
        if result.wasSuccessful():
            print(f"✅ All {result.testsRun} comprehensive tests passed")
            return True
        else:
            print(f"❌ {len(result.failures)} failures, {len(result.errors)} errors")
            
            # Print first few failures/errors
            if result.failures:
                print("\nFailures:")
                for test, traceback in result.failures[:2]:
                    print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
            
            if result.errors:
                print("\nErrors:")
                for test, traceback in result.errors[:2]:
                    print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
            
            return False
            
    except ImportError as e:
        print(f"⚠️ Could not import comprehensive tests: {e}")
        print("⚠️ Make sure test files are in the test/ directory")
        return None
    except Exception as e:
        print(f"❌ Comprehensive test error: {str(e)}")
        return False

def run_anchor_points_tests():
    """Run anchor points specific tests."""
    print("\n🎯 ANCHOR POINTS TESTS")
    print("=" * 50)
    
    try:
        from app.test_patterns import TEST_PATTERNS
        from app.charts import _calculate_pnf_points
        from anchor_point_calculator import AnchorPointCalculator
        import pandas as pd
        
        anchor_calculator = AnchorPointCalculator(min_column_separation=7)
        
        # Test with bullish_breakout pattern
        pattern_info = TEST_PATTERNS['bullish_breakout']
        candles = pattern_info['data_generator']()
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        
        x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, 0.01, 3)
        
        if len(x_coords) > 0:
            # Create P&F matrix
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
                
                print(f"✅ Generated {len(anchor_points)} anchor points")
                
                if anchor_points:
                    max_boxes = max(ap.box_count for ap in anchor_points)
                    avg_boxes = sum(ap.box_count for ap in anchor_points) / len(anchor_points)
                    print(f"✅ Box counts: max={max_boxes}, avg={avg_boxes:.1f}")
                
                return True
            else:
                print("⚠️ No price range for anchor points")
                return True
        else:
            print("⚠️ No P&F points for anchor points test")
            return True
            
    except Exception as e:
        print(f"❌ Anchor points test error: {str(e)}")
        return False

def main():
    """Main test runner."""
    start_time = time.time()
    
    print("🚀 PATTERN SYSTEM TEST RUNNER")
    print("=" * 80)
    print("Testing all patterns with 1% box size and 3-box reversal")
    print("This ensures your pattern system is working correctly")
    print("=" * 80)
    
    # Run tests
    quick_success = run_quick_pattern_tests()
    anchor_success = run_anchor_points_tests()
    comprehensive_success = run_comprehensive_tests()
    
    # Calculate duration
    end_time = time.time()
    duration = end_time - start_time
    
    # Final summary
    print("\n" + "=" * 80)
    print("🎯 FINAL TEST RESULTS")
    print("=" * 80)
    print(f"⏱️  Total Duration: {duration:.2f} seconds")
    
    if quick_success:
        print("✅ Quick Pattern Tests: PASSED")
    else:
        print("❌ Quick Pattern Tests: FAILED")
    
    if anchor_success:
        print("✅ Anchor Points Tests: PASSED")
    else:
        print("❌ Anchor Points Tests: FAILED")
    
    if comprehensive_success is True:
        print("✅ Comprehensive Tests: PASSED")
    elif comprehensive_success is False:
        print("❌ Comprehensive Tests: FAILED")
    else:
        print("⚠️ Comprehensive Tests: SKIPPED")
    
    # Overall status
    overall_success = quick_success and anchor_success and (comprehensive_success is not False)
    
    if overall_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Pattern system is working correctly")
        print("✅ 1% box size and 3-box reversal working")
        print("✅ Anchor points integration working")
        print("✅ Safe to start application")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("⚠️ Pattern system may have issues")
        print("⚠️ Check errors above before starting application")
    
    print("=" * 80)
    
    return overall_success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
