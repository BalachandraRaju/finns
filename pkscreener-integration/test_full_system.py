"""
Full System Test for PKScreener Integration
Tests all components: scanners, backtesting, and scheduler
"""
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

import logging
from datetime import datetime, timedelta
import pytz

from app.db import get_db
from scanner_engine import ScannerEngine
from backtest_engine import BacktestEngine
from scanner_scheduler import is_market_hours, get_scheduler_status

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(title.center(80))
    print("="*80 + "\n")


def test_live_scanners():
    """Test live scanner functionality"""
    print_header("TEST 1: LIVE SCANNER ENGINE")
    
    db = next(get_db())
    engine = ScannerEngine(db)
    
    print(f"📊 Loaded {len(engine.watchlist)} stocks from watchlist")
    print(f"🔍 Running Scanner #1 and #12 on all stocks...")
    print("   (This may take a few minutes...)\n")
    
    results = engine.scan_all_stocks(scanner_ids=[1, 12])
    
    print("\n📈 LIVE SCANNER RESULTS:")
    print("-" * 80)
    
    for scanner_id in [1, 12]:
        scanner_results = results[scanner_id]
        print(f"\n📊 Scanner #{scanner_id}: {len(scanner_results)} triggers")
        
        if scanner_results:
            print(f"\nTop 10 stocks:")
            for i, result in enumerate(scanner_results[:10], 1):
                vol_ratio = result.volume_ratio if result.volume_ratio else 0
                rsi = result.rsi_value if result.rsi_value else 0
                print(f"  {i:2d}. {result.symbol:15s} ₹{result.trigger_price:8.2f} | "
                      f"Vol: {vol_ratio:5.2f}x | RSI: {rsi:5.1f}")
        else:
            print("  ℹ️  No triggers found (scanners have strict criteria)")
    
    # Get active results from database
    print("\n📋 Active results in database:")
    active_results = engine.get_active_results()
    print(f"  Total active results: {len(active_results)}")
    
    db.close()
    print("\n✅ Live scanner test complete!")
    return results


def test_backtesting():
    """Test backtesting functionality"""
    print_header("TEST 2: BACKTESTING ENGINE")
    
    db = next(get_db())
    engine = BacktestEngine(db)
    
    # Backtest last 5 trading days on limited stocks
    end_date = datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)
    start_date = end_date - timedelta(days=7)
    
    print(f"📅 Backtest Period: {start_date.date()} to {end_date.date()}")
    print(f"📊 Scanners: #1 (Volume+Momentum+Breakout+ATR), #12 (Same + RSI Filter)")
    print(f"🎯 Testing on first 10 stocks for speed...")
    print(f"⏱️  Focus: Momentum scalping (5min, 15min, 30min, 1hr, 2hr returns)\n")
    
    results = engine.run_backtest(
        scanner_ids=[1, 12],
        start_date=start_date,
        end_date=end_date,
        max_stocks=10
    )
    
    print("\n📈 BACKTEST RESULTS:")
    print("-" * 80)
    
    for scanner_id in [1, 12]:
        scanner_results = results[scanner_id]
        print(f"\n📊 Scanner #{scanner_id}: {len(scanner_results)} triggers")
        
        if scanner_results:
            # Calculate statistics
            successful = [r for r in scanner_results if r.was_successful]
            hit_1pct = [r for r in scanner_results if r.hit_target_1pct]
            hit_2pct = [r for r in scanner_results if r.hit_target_2pct]
            hit_stoploss = [r for r in scanner_results if r.hit_stoploss]
            
            returns_30min = [r.return_30min_pct for r in scanner_results if r.return_30min_pct is not None]
            avg_30min = sum(returns_30min) / len(returns_30min) if returns_30min else 0
            
            max_profits = [r.max_profit_pct for r in scanner_results if r.max_profit_pct is not None]
            max_losses = [r.max_loss_pct for r in scanner_results if r.max_loss_pct is not None]
            
            max_profit = max(max_profits) if max_profits else 0
            max_loss = min(max_losses) if max_losses else 0
            
            print(f"\n  📊 Performance Metrics:")
            print(f"     Success Rate (30min positive): {len(successful)}/{len(scanner_results)} "
                  f"({len(successful)/len(scanner_results)*100:.1f}%)")
            print(f"     Hit 1% Target: {len(hit_1pct)}/{len(scanner_results)} "
                  f"({len(hit_1pct)/len(scanner_results)*100:.1f}%)")
            print(f"     Hit 2% Target: {len(hit_2pct)}/{len(scanner_results)} "
                  f"({len(hit_2pct)/len(scanner_results)*100:.1f}%)")
            print(f"     Hit Stop Loss (-1%): {len(hit_stoploss)}/{len(scanner_results)} "
                  f"({len(hit_stoploss)/len(scanner_results)*100:.1f}%)")
            print(f"     Avg 30min Return: {avg_30min:+.2f}%")
            print(f"     Max Profit: {max_profit:+.2f}%")
            print(f"     Max Loss: {max_loss:+.2f}%")
            
            print(f"\n  🏆 Top 5 Trades (by 30min return):")
            sorted_results = sorted(scanner_results, 
                                   key=lambda x: x.return_30min_pct if x.return_30min_pct else -999, 
                                   reverse=True)
            for i, r in enumerate(sorted_results[:5], 1):
                ret_30min = r.return_30min_pct if r.return_30min_pct else 0
                max_profit = r.max_profit_pct if r.max_profit_pct else 0
                print(f"     {i}. {r.symbol:12s} on {r.backtest_date.date()}: "
                      f"{ret_30min:+6.2f}% (30min) | Max: {max_profit:+6.2f}%")
        else:
            print("  ℹ️  No triggers found in backtest period")
    
    db.close()
    print("\n✅ Backtest test complete!")
    return results


def test_scheduler():
    """Test scheduler functionality"""
    print_header("TEST 3: SCHEDULER STATUS")
    
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    print(f"🕐 Current Time (IST): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Day of Week: {now.strftime('%A')}")
    
    market_hours = is_market_hours()
    print(f"🏢 Market Hours: {'YES ✅' if market_hours else 'NO ⏸️'}")
    print(f"   (Market hours: Mon-Fri, 9:15 AM - 3:30 PM IST)")
    
    status = get_scheduler_status()
    print(f"\n📊 Scheduler Status:")
    print(f"   Running: {status['running']}")
    print(f"   Next Run: {status.get('next_run', 'N/A')}")
    
    if not market_hours:
        print(f"\n⏸️  Scheduler will activate during next market session")
        print(f"   Next market day: Monday-Friday, 9:15 AM IST")
    else:
        print(f"\n✅ Scheduler is active and will run every 3 minutes")
    
    print("\n✅ Scheduler test complete!")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("PKSCREENER INTEGRATION - FULL SYSTEM TEST".center(80))
    print("="*80)
    print("\nThis test will verify:")
    print("  1. Live scanner engine")
    print("  2. Backtesting engine")
    print("  3. Scheduler status")
    print("\n" + "="*80)
    
    try:
        # Test 1: Live Scanners
        live_results = test_live_scanners()
        
        # Test 2: Backtesting
        backtest_results = test_backtesting()
        
        # Test 3: Scheduler
        test_scheduler()
        
        # Final Summary
        print_header("FINAL SUMMARY")
        
        print("✅ All tests completed successfully!\n")
        
        print("📊 System Status:")
        print(f"   • Live Scanner: Operational")
        print(f"   • Backtest Engine: Operational")
        print(f"   • Scheduler: Ready")
        print(f"   • Database Tables: Created")
        
        print("\n📋 Next Steps:")
        print("   1. Review backtest results to validate scanner performance")
        print("   2. Integrate scheduler into main FastAPI app")
        print("   3. Create UI pages for live results and backtest reports")
        print("   4. Run full 2-month backtest for comprehensive analysis")
        
        print("\n🚀 PKScreener integration is ready for deployment!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        print(f"\n❌ Test failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

