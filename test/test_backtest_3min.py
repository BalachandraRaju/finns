#!/usr/bin/env python3
"""
Test script to verify backtest engine generates 3min interval alerts correctly
"""
import sys
sys.path.insert(0, 'pkscreener-integration')
sys.path.insert(0, '.')

from datetime import datetime, timedelta
from backtest_engine import BacktestEngine
from app.db import get_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_backtest_3min_alerts():
    """Test that backtest generates 3min interval alerts"""
    print("\n" + "="*80)
    print("TESTING PKSCREENER BACKTEST - 3MIN INTERVAL ALERTS")
    print("="*80)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Initialize backtest engine
        engine = BacktestEngine(db)
        
        # Test with last week on more stocks
        end_date = datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)
        start_date = end_date - timedelta(days=7)  # Last week

        print(f"\n📅 Backtest Period: {start_date.date()} to {end_date.date()}")
        print(f"📊 Testing Scanners: #1, #12, #14, #20, #21")
        print(f"🎯 Testing on first 50 stocks...")
        print("\n" + "-"*80)

        # Run backtest
        results = engine.run_backtest(
            scanner_ids=[1, 12, 14, 20, 21],
            start_date=start_date,
            end_date=end_date,
            max_stocks=50  # Test on 50 stocks
        )
        
        # Analyze results
        print("\n" + "="*80)
        print("BACKTEST RESULTS ANALYSIS")
        print("="*80)
        
        total_alerts = 0
        alerts_with_3min = 0
        
        for scanner_id, scanner_results in results.items():
            print(f"\n📊 Scanner #{scanner_id}:")
            print(f"   Total Alerts: {len(scanner_results)}")
            
            if scanner_results:
                # Check 3min data
                has_3min_price = sum(1 for r in scanner_results if r.price_after_3min is not None)
                has_3min_return = sum(1 for r in scanner_results if r.return_3min_pct is not None)
                
                print(f"   Alerts with 3min price: {has_3min_price}/{len(scanner_results)}")
                print(f"   Alerts with 3min return: {has_3min_return}/{len(scanner_results)}")
                
                # Show sample alerts
                if len(scanner_results) > 0:
                    print(f"\n   Sample Alerts (first 3):")
                    for i, result in enumerate(scanner_results[:3], 1):
                        print(f"   {i}. {result.symbol} @ {result.trigger_time.strftime('%Y-%m-%d %H:%M')}")
                        print(f"      Trigger Price: ₹{result.trigger_price:.2f}")
                        if result.price_after_3min:
                            print(f"      Price after 3min: ₹{result.price_after_3min:.2f}")
                        if result.return_3min_pct is not None:
                            print(f"      Return 3min: {result.return_3min_pct:.2f}%")
                        if result.return_5min_pct is not None:
                            print(f"      Return 5min: {result.return_5min_pct:.2f}%")
                        if result.return_15min_pct is not None:
                            print(f"      Return 15min: {result.return_15min_pct:.2f}%")
                        print()
                
                total_alerts += len(scanner_results)
                alerts_with_3min += has_3min_return
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"✅ Total Alerts Generated: {total_alerts}")
        print(f"✅ Alerts with 3min data: {alerts_with_3min}")
        
        if total_alerts > 0:
            coverage = (alerts_with_3min / total_alerts) * 100
            print(f"✅ 3min Data Coverage: {coverage:.1f}%")
            
            if coverage >= 80:
                print("\n🎉 SUCCESS! 3min interval alerts are working correctly!")
                return True
            else:
                print("\n⚠️  WARNING: Low 3min data coverage. Some alerts may not have 3min data.")
                print("   This could be due to:")
                print("   - Alerts triggered near market close (no 3min future data)")
                print("   - Missing 1-minute candle data")
                return False
        else:
            print("\n⚠️  No alerts generated. This could mean:")
            print("   - No stocks met scanner criteria in the test period")
            print("   - Insufficient historical data")
            print("   - Scanner conditions are too strict")
            return False
            
    except Exception as e:
        logger.error(f"Error running backtest: {e}", exc_info=True)
        print(f"\n❌ ERROR: {e}")
        return False
    finally:
        db.close()

if __name__ == '__main__':
    success = test_backtest_3min_alerts()
    sys.exit(0 if success else 1)

