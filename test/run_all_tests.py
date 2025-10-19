#!/usr/bin/env python3
"""
Master test runner for all pattern test suites.
Runs comprehensive tests to ensure all patterns work correctly with 1% box size and 3-box reversal.
This should be run before any deployment or major changes.
"""

import sys
import os
import unittest
import time
from io import StringIO

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import all test modules
from test_all_patterns_comprehensive import TestAllPatternsComprehensive
from test_pattern_alerts import TestPatternAlerts
from test_anchor_points_patterns import TestAnchorPointsPatterns
from test_chart_generation import TestChartGeneration

class TestResults:
    """Class to track test results across all suites."""
    
    def __init__(self):
        self.total_tests = 0
        self.total_failures = 0
        self.total_errors = 0
        self.suite_results = {}
        self.start_time = None
        self.end_time = None
    
    def add_suite_result(self, suite_name: str, result: unittest.TestResult):
        """Add results from a test suite."""
        self.suite_results[suite_name] = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.wasSuccessful()
        }
        
        self.total_tests += result.testsRun
        self.total_failures += len(result.failures)
        self.total_errors += len(result.errors)
    
    def print_summary(self):
        """Print comprehensive test summary."""
        duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        print("\n" + "=" * 80)
        print("🎯 COMPREHENSIVE PATTERN TEST RESULTS")
        print("=" * 80)
        print(f"⏱️  Total Duration: {duration:.2f} seconds")
        print(f"📊 Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.total_tests - self.total_failures - self.total_errors}")
        print(f"❌ Failed: {self.total_failures}")
        print(f"💥 Errors: {self.total_errors}")
        print()
        
        # Suite-by-suite breakdown
        print("📋 SUITE BREAKDOWN:")
        print("-" * 60)
        for suite_name, results in self.suite_results.items():
            status = "✅ PASS" if results['success'] else "❌ FAIL"
            print(f"{status} {suite_name}")
            print(f"     Tests: {results['tests_run']}, "
                  f"Failures: {results['failures']}, "
                  f"Errors: {results['errors']}")
        
        print()
        
        # Overall status
        overall_success = self.total_failures == 0 and self.total_errors == 0
        if overall_success:
            print("🎉 ALL TESTS PASSED!")
            print("✅ All patterns work correctly with 1% box size and 3-box reversal")
            print("✅ Anchor points integration working")
            print("✅ Pattern detection functioning")
            print("✅ Chart generation compatible")
            print("✅ Alert generation working")
            print("✅ Code is stable and ready for production")
        else:
            print("❌ SOME TESTS FAILED!")
            print("⚠️  Please fix issues before deploying changes")
            print("⚠️  Check individual test outputs for details")
        
        return overall_success


def run_test_suite(suite_class, suite_name: str, verbose: bool = True) -> unittest.TestResult:
    """Run a specific test suite and return results."""
    print(f"\n{'='*20} {suite_name} {'='*20}")
    print(f"Running {suite_name}...")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(suite_class)
    
    # Capture output if not verbose
    if verbose:
        stream = sys.stdout
    else:
        stream = StringIO()
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1, stream=stream)
    result = runner.run(suite)
    
    # Print summary for this suite
    if result.wasSuccessful():
        print(f"✅ {suite_name}: All {result.testsRun} tests passed")
    else:
        print(f"❌ {suite_name}: {len(result.failures)} failures, {len(result.errors)} errors")
    
    return result


def main():
    """Main test runner function."""
    print("🚀 STARTING COMPREHENSIVE PATTERN TEST SUITE")
    print("=" * 80)
    print("This test suite ensures all patterns work correctly and prevents regressions.")
    print("Testing with 1% box size and 3-box reversal as specified.")
    print("=" * 80)
    
    # Initialize results tracker
    results = TestResults()
    results.start_time = time.time()
    
    # Define test suites to run
    test_suites = [
        (TestAllPatternsComprehensive, "Comprehensive Pattern Tests"),
        (TestPatternAlerts, "Pattern Alert Tests"),
        (TestAnchorPointsPatterns, "Anchor Points Integration Tests"),
        (TestChartGeneration, "Chart Generation Tests")
    ]
    
    # Run each test suite
    for suite_class, suite_name in test_suites:
        try:
            result = run_test_suite(suite_class, suite_name, verbose=True)
            results.add_suite_result(suite_name, result)
        except Exception as e:
            print(f"❌ Error running {suite_name}: {str(e)}")
            # Create a dummy failed result
            dummy_result = unittest.TestResult()
            dummy_result.testsRun = 1
            dummy_result.errors = [(None, str(e))]
            results.add_suite_result(suite_name, dummy_result)
    
    results.end_time = time.time()
    
    # Print comprehensive summary
    overall_success = results.print_summary()
    
    # Additional recommendations
    print("\n" + "=" * 80)
    print("💡 RECOMMENDATIONS:")
    print("=" * 80)
    
    if overall_success:
        print("🎯 Your pattern system is working perfectly!")
        print("📊 All patterns generate valid P&F charts")
        print("🎯 Anchor points are calculating correctly")
        print("🚨 Alert system is functioning properly")
        print("📈 Chart generation is compatible")
        print()
        print("✅ Safe to deploy changes")
        print("✅ Safe to modify patterns")
        print("✅ System is production-ready")
    else:
        print("⚠️  Issues detected in pattern system!")
        print("🔧 Fix failing tests before deployment")
        print("📋 Review test output for specific issues")
        print("🧪 Re-run tests after fixes")
        print()
        print("❌ Do not deploy until all tests pass")
    
    print("\n" + "=" * 80)
    print("🎯 TEST SUITE COMPLETE")
    print("=" * 80)
    
    return overall_success


if __name__ == '__main__':
    success = main()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
