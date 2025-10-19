#!/usr/bin/env python3
"""
Comprehensive Pattern Validation Script
Tests all 18 pattern types with 0.25% box size and 3-box reversal.
"""

import sys
sys.path.append('/Users/balachandra.raju/projects/finns')

from app.test_patterns import TEST_PATTERNS, analyze_alert_triggers
from app.charts import _calculate_pnf_points
from app.pattern_detector import PatternDetector, PatternType

# PRODUCTION SETTINGS
BOX_SIZE = 0.0025  # 0.25%
REVERSAL = 3       # 3-box reversal

def test_pattern(pattern_key: str, pattern_info: dict) -> dict:
    """Test a single pattern and return results."""
    print(f"\n{'='*70}")
    print(f"🧪 Testing: {pattern_info['name']}")
    print(f"{'='*70}")
    
    # Generate pattern data
    candles = pattern_info['data_generator']()
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    closes = [c['close'] for c in candles]
    
    # Calculate P&F points
    x_coords, y_coords, pnf_symbols = _calculate_pnf_points(highs, lows, BOX_SIZE, REVERSAL)
    
    # Analyze alerts
    analysis = analyze_alert_triggers(highs, lows, BOX_SIZE, REVERSAL, pattern_key, closes)
    
    # Print results
    print(f"📊 Pattern Data:")
    print(f"   Candles: {len(candles)}")
    print(f"   P&F Points: {len(x_coords)}")
    print(f"   Columns: {max(x_coords) if x_coords else 0}")
    print(f"   Expected Signal: {pattern_info['expected_signal']}")
    
    print(f"\n🚨 Alert Detection:")
    print(f"   Alerts Detected: {analysis['alert_count']}")
    print(f"   Patterns Confirmed: {analysis['unique_patterns_detected']}")
    
    # Detailed alert information
    if analysis['triggers']:
        print(f"\n   Alert Details:")
        for i, trigger in enumerate(analysis['triggers'], 1):
            print(f"   {i}. {trigger['type']}")
            print(f"      Signal: {trigger['signal']} at column {trigger['column']}, price {trigger['price']:.2f}")
            print(f"      Description: {trigger['description'][:100]}...")
    else:
        print(f"   ⚠️  NO ALERTS DETECTED!")
    
    # Pattern states
    if analysis['pattern_states']:
        print(f"\n   Confirmed Patterns:")
        for ptype, pstate in analysis['pattern_states'].items():
            if pstate['confirmed']:
                print(f"   ✅ {ptype}: Confirmed at {pstate['confirmation_price']:.2f}")
    
    # Determine status
    status = "✅ PASS" if analysis['alert_count'] > 0 else "❌ FAIL"
    expected_match = "✅" if any(pattern_info['expected_signal'] in t['signal'] for t in analysis['triggers']) else "⚠️"
    
    print(f"\n{status} - Expected: {pattern_info['expected_signal']}, Match: {expected_match}")
    
    return {
        'pattern_key': pattern_key,
        'pattern_name': pattern_info['name'],
        'expected_signal': pattern_info['expected_signal'],
        'candles': len(candles),
        'pnf_points': len(x_coords),
        'columns': max(x_coords) if x_coords else 0,
        'alerts_detected': analysis['alert_count'],
        'patterns_confirmed': analysis['unique_patterns_detected'],
        'status': 'PASS' if analysis['alert_count'] > 0 else 'FAIL',
        'triggers': analysis['triggers']
    }

def main():
    """Run comprehensive pattern validation."""
    print("\n" + "="*70)
    print("🎯 COMPREHENSIVE PATTERN VALIDATION")
    print("="*70)
    print(f"Box Size: {BOX_SIZE*100:.2f}% (0.25% PRODUCTION SETTING)")
    print(f"Reversal: {REVERSAL}-box reversal")
    print(f"Total Patterns: {len(TEST_PATTERNS)}")
    print("="*70)
    
    results = []
    
    # Test all patterns
    for pattern_key, pattern_info in TEST_PATTERNS.items():
        try:
            result = test_pattern(pattern_key, pattern_info)
            results.append(result)
        except Exception as e:
            print(f"\n❌ ERROR testing {pattern_key}: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'pattern_key': pattern_key,
                'pattern_name': pattern_info['name'],
                'status': 'ERROR',
                'error': str(e)
            })
    
    # Summary
    print("\n" + "="*70)
    print("📊 VALIDATION SUMMARY")
    print("="*70)
    
    passed = sum(1 for r in results if r.get('status') == 'PASS')
    failed = sum(1 for r in results if r.get('status') == 'FAIL')
    errors = sum(1 for r in results if r.get('status') == 'ERROR')
    
    print(f"\nTotal Patterns: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Errors: {errors}")
    print(f"Success Rate: {(passed/len(results)*100):.1f}%")
    
    # Failed patterns
    if failed > 0:
        print(f"\n❌ Failed Patterns:")
        for r in results:
            if r.get('status') == 'FAIL':
                print(f"   - {r['pattern_name']} ({r['pattern_key']})")
                print(f"     Expected: {r['expected_signal']}, Detected: {r['alerts_detected']} alerts")
    
    # Error patterns
    if errors > 0:
        print(f"\n⚠️  Error Patterns:")
        for r in results:
            if r.get('status') == 'ERROR':
                print(f"   - {r['pattern_name']} ({r['pattern_key']})")
                print(f"     Error: {r.get('error', 'Unknown')}")
    
    print("\n" + "="*70)
    
    # Return exit code
    return 0 if failed == 0 and errors == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

