#!/usr/bin/env python3
"""
Quick test to verify all 21 scanners are properly implemented and accessible
"""
import sys
sys.path.insert(0, '.')

from pkscreener-integration.scanner_strategies import ScannerStrategies
from pkscreener-integration.technical_indicators import TechnicalIndicators
import pandas as pd
import numpy as np

def create_dummy_df():
    """Create a dummy dataframe with 100 candles for testing"""
    dates = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='1min')
    df = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.uniform(100, 110, 100),
        'high': np.random.uniform(110, 115, 100),
        'low': np.random.uniform(95, 100, 100),
        'close': np.random.uniform(100, 110, 100),
        'volume': np.random.uniform(10000, 50000, 100)
    })
    # Sort by timestamp descending (most recent first)
    df = df.sort_values('timestamp', ascending=False).reset_index(drop=True)
    return df

def test_all_scanners():
    """Test that all 21 scanners are accessible and callable"""
    ti = TechnicalIndicators()
    strategies = ScannerStrategies(ti)
    df = create_dummy_df()
    
    scanner_methods = [
        (1, 'scanner_1_volume_momentum_breakout_atr'),
        (2, 'scanner_2_volume_momentum_atr'),
        (3, 'scanner_3_volume_momentum'),
        (4, 'scanner_4_volume_atr'),
        (5, 'scanner_5_volume_bidask'),
        (6, 'scanner_6_volume_atr_trailing'),
        (7, 'scanner_7_volume_trailing'),
        (8, 'scanner_8_momentum_atr'),
        (9, 'scanner_9_momentum_trailing'),
        (10, 'scanner_10_atr_trailing'),
        (11, 'scanner_11_ttm_squeeze_rsi'),
        (12, 'scanner_12_volume_momentum_breakout_atr_rsi'),
        (13, 'scanner_13_volume_atr_rsi'),
        (14, 'scanner_14_vcp_chart_patterns_ma_support'),
        (15, 'scanner_15_vcp_patterns_ma'),
        (16, 'scanner_16_breakout_vcp_patterns_ma'),
        (17, 'scanner_17_trailing_vcp'),
        (18, 'scanner_18_vcp_trailing'),
        (19, 'scanner_19_nifty_vcp_trailing'),
        (20, 'scanner_20_comprehensive'),
        (21, 'scanner_21_bullcross_ma_fair_value'),
    ]
    
    print("=" * 80)
    print("TESTING ALL 21 PKSCREENER SCANNERS")
    print("=" * 80)
    
    passed_count = 0
    failed_count = 0
    
    for scanner_id, method_name in scanner_methods:
        try:
            # Check if method exists
            if not hasattr(strategies, method_name):
                print(f"❌ Scanner #{scanner_id:2d} - Method '{method_name}' NOT FOUND")
                failed_count += 1
                continue
            
            # Try to call the method
            method = getattr(strategies, method_name)
            result = method(df)
            
            # Verify return type
            if not isinstance(result, tuple) or len(result) != 2:
                print(f"❌ Scanner #{scanner_id:2d} - Invalid return type: {type(result)}")
                failed_count += 1
                continue
            
            passed, metrics = result
            
            # Verify return values
            if not isinstance(passed, bool):
                print(f"❌ Scanner #{scanner_id:2d} - Invalid 'passed' type: {type(passed)}")
                failed_count += 1
                continue
            
            if not isinstance(metrics, dict):
                print(f"❌ Scanner #{scanner_id:2d} - Invalid 'metrics' type: {type(metrics)}")
                failed_count += 1
                continue
            
            # Success!
            status = "✅ PASS" if passed else "⚪ FAIL"
            print(f"{status} Scanner #{scanner_id:2d} - {method_name}")
            passed_count += 1
            
        except Exception as e:
            print(f"❌ Scanner #{scanner_id:2d} - Exception: {str(e)[:60]}")
            failed_count += 1
    
    print("=" * 80)
    print(f"RESULTS: {passed_count}/21 scanners accessible and callable")
    if failed_count > 0:
        print(f"⚠️  {failed_count} scanners had issues")
    else:
        print("✅ ALL 21 SCANNERS WORKING!")
    print("=" * 80)
    
    return failed_count == 0

if __name__ == '__main__':
    success = test_all_scanners()
    sys.exit(0 if success else 1)

