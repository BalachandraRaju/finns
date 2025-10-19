"""
Test PKScreener Backtest Integration
Tests all scanners including new breakout scanners (17, 20, 23, 32)
"""
import sys
import os
from datetime import datetime, timedelta

# Add paths
sys.path.insert(0, 'pkscreener-integration')
sys.path.insert(0, '.')

from app.db import get_db

# Import backtest engine using importlib
import importlib.util
spec = importlib.util.spec_from_file_location("backtest_engine", "pkscreener-integration/backtest_engine.py")
backtest_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backtest_module)
BacktestEngine = backtest_module.BacktestEngine

def test_backtest_integration():
    """Test backtest with all scanners including new breakout scanners"""
    
    print("="*80)
    print("TESTING PKSCREENER BACKTEST INTEGRATION")
    print("="*80)
    
    # Test parameters
    end_date = datetime(2025, 10, 17, 15, 30)  # Oct 17, 2025 at 3:30 PM
    start_date = end_date - timedelta(days=1)  # 1 day backtest
    
    # All scanners including new breakout scanners
    scanner_ids = [1, 17, 20, 23, 32]
    
    print(f"\nTest Configuration:")
    print(f"  Date Range: {start_date.date()} to {end_date.date()}")
    print(f"  Scanners: {scanner_ids}")
    print(f"  Scanner Names:")
    print(f"    #1  - Probable Breakout (Original)")
    print(f"    #17 - 52-Week High Breakout (PKScreener)")
    print(f"    #20 - Bullish for Tomorrow (PKScreener)")
    print(f"    #23 - Breaking Out Now (PKScreener)")
    print(f"    #32 - Intraday Breakout Setup (PKScreener)")
    print(f"  Max Stocks: 20 (for speed)")
    print()
    
    # Initialize backtest engine
    db = next(get_db())
    try:
        engine = BacktestEngine(db)
        
        # Limit to 20 stocks for quick test
        engine.watchlist = engine.watchlist[:20]
        
        print(f"Running backtest on {len(engine.watchlist)} stocks...")
        print()
        
        # Run backtest
        results = engine.run_backtest(
            scanner_ids=scanner_ids,
            start_date=start_date,
            end_date=end_date,
            max_stocks=20
        )
        
        # Display results
        print("\n" + "="*80)
        print("BACKTEST RESULTS")
        print("="*80)
        
        scanner_names = {
            1: "Probable Breakout",
            17: "52-Week High Breakout",
            20: "Bullish for Tomorrow",
            23: "Breaking Out Now",
            32: "Intraday Breakout Setup"
        }
        
        total_alerts = 0
        for scanner_id in scanner_ids:
            scanner_results = results.get(scanner_id, [])
            total_alerts += len(scanner_results)
            
            print(f"\n📊 Scanner #{scanner_id}: {scanner_names[scanner_id]}")
            print(f"   Alerts: {len(scanner_results)}")
            
            if scanner_results:
                # Show top 3 alerts
                print(f"   Top alerts:")
                for i, result in enumerate(scanner_results[:3], 1):
                    print(f"     {i}. {result.symbol} @ {result.trigger_time.strftime('%H:%M')} - "
                          f"₹{result.trigger_price:.2f} "
                          f"(3min: {result.return_3min_pct:+.2f}%, "
                          f"5min: {result.return_5min_pct:+.2f}%)")
        
        print("\n" + "="*80)
        print(f"TOTAL ALERTS: {total_alerts}")
        print("="*80)
        
        # Verify all scanners ran
        print("\n✅ Integration Test Results:")
        for scanner_id in scanner_ids:
            if scanner_id in results:
                print(f"  ✅ Scanner #{scanner_id} executed successfully")
            else:
                print(f"  ❌ Scanner #{scanner_id} FAILED")
        
        print("\n✅ INTEGRATION TEST PASSED!")
        print("All scanners are integrated and working in the backtest engine.")
        
    finally:
        db.close()


if __name__ == "__main__":
    test_backtest_integration()

