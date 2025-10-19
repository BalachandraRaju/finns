"""
Test PKScreener Backtesting on CDSL Stock
Tests the improved backtesting system with 2 months of CDSL data
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
from sqlalchemy import text
import json
import redis

from app.db import get_db
from backtest_engine import BacktestEngine

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


def main():
    """Run CDSL backtest"""
    print_header("CDSL STOCK BACKTEST - 2 MONTHS")
    
    db = next(get_db())
    
    # Get CDSL from watchlist
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    watchlist_json = r.get('watchlist')
    
    if not watchlist_json:
        print("❌ No watchlist found in Redis")
        db.close()
        return
    
    watchlist = json.loads(watchlist_json)
    
    # Find CDSL
    cdsl_stock = None
    for stock in watchlist:
        if stock.get('symbol') == 'CDSL':
            cdsl_stock = stock
            break
    
    if not cdsl_stock:
        print("❌ CDSL not found in watchlist")
        print("\nAvailable stocks with 'CD' in name:")
        for stock in watchlist:
            if 'CD' in stock.get('symbol', ''):
                print(f"  - {stock['symbol']} ({stock['instrument_key']})")
        db.close()
        return
    
    print(f"✅ Found CDSL in watchlist:")
    print(f"   Symbol: {cdsl_stock['symbol']}")
    print(f"   Instrument Key: {cdsl_stock['instrument_key']}")
    print(f"   Exchange: {cdsl_stock.get('exchange', 'N/A')}")
    
    # Check candle data
    instrument_key = cdsl_stock['instrument_key']
    result = db.execute(text('''
        SELECT 
            instrument_key,
            COUNT(*) as candle_count,
            MIN(timestamp) as first_candle,
            MAX(timestamp) as last_candle,
            DATE(MIN(timestamp)) as first_date,
            DATE(MAX(timestamp)) as last_date
        FROM candles 
        WHERE instrument_key = :key
        AND interval = '1'
        GROUP BY instrument_key
    '''), {'key': instrument_key}).fetchone()
    
    if not result:
        print(f"\n❌ No candle data found for CDSL ({instrument_key})")
        print("Run backfill first: python3 backfill_all_stocks.py")
        db.close()
        return
    
    print(f"\n📊 Candle Data:")
    print(f"   Total Candles: {result[1]:,}")
    print(f"   First Candle: {result[2]}")
    print(f"   Last Candle: {result[3]}")
    print(f"   Date Range: {result[4]} to {result[5]}")
    
    # Calculate days of data
    first = datetime.strptime(result[4], '%Y-%m-%d')
    last = datetime.strptime(result[5], '%Y-%m-%d')
    days = (last - first).days
    print(f"   Days of Data: {days} days")
    
    # Check recent data (last 60 days)
    sixty_days_ago = datetime.now() - timedelta(days=60)
    recent = db.execute(text('''
        SELECT COUNT(*) 
        FROM candles 
        WHERE instrument_key = :key
        AND interval = '1'
        AND timestamp >= :date
    '''), {'key': instrument_key, 'date': sixty_days_ago}).fetchone()[0]
    
    print(f"   Last 60 Days: {recent:,} candles")
    
    if recent < 1000:
        print(f"\n⚠️  Warning: Only {recent} candles in last 60 days")
        print("   Recommend running backfill for better results")
    
    # Set backtest period to last 60 days
    end_date = datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)
    start_date = end_date - timedelta(days=60)
    
    print(f"\n📅 Backtest Period:")
    print(f"   Start: {start_date.date()}")
    print(f"   End: {end_date.date()}")
    print(f"   Duration: 60 days (~2 months)")
    
    print(f"\n🔍 Scanners to Test:")
    print(f"   Scanner #1: Volume + Momentum + Breakout + ATR")
    print(f"   Scanner #12: Scanner #1 + RSI Filter (0-54)")
    
    print(f"\n⏱️  Backtest Configuration:")
    print(f"   ✅ Checks EVERY MINUTE (not every 30 minutes)")
    print(f"   ✅ 3-minute interval returns (critical for scalping)")
    print(f"   ✅ Captures ALL triggers (30min gap between)")
    print(f"   ✅ Exact trigger point detection")
    
    print(f"\n🚀 Starting backtest...")
    print(f"   This may take 1-2 minutes...\n")
    
    # Create temporary watchlist with just CDSL
    temp_watchlist = [cdsl_stock]
    
    # Save to Redis temporarily
    r.set('temp_cdsl_watchlist', json.dumps(temp_watchlist))
    
    # Run backtest
    engine = BacktestEngine(db)
    
    # Manually override the watchlist loading
    engine.stocks = temp_watchlist
    
    results = engine.run_backtest(
        scanner_ids=[1, 12],
        start_date=start_date,
        end_date=end_date,
        max_stocks=1  # Just CDSL
    )
    
    print_header("BACKTEST RESULTS - CDSL")
    
    for scanner_id in [1, 12]:
        scanner_results = results[scanner_id]
        
        print(f"\n{'='*80}")
        print(f"SCANNER #{scanner_id}")
        print(f"{'='*80}")
        
        if not scanner_results:
            print("❌ No triggers found")
            print("ℹ️  Possible reasons:")
            print("   - Scanner criteria are strict (by design)")
            print("   - CDSL didn't meet volume/momentum requirements")
            print("   - No strong breakout patterns in this period")
            continue
        
        # Calculate statistics
        total_triggers = len(scanner_results)
        
        # Success metrics
        successful = [r for r in scanner_results if r.was_successful]
        hit_1pct = [r for r in scanner_results if r.hit_target_1pct]
        hit_2pct = [r for r in scanner_results if r.hit_target_2pct]
        hit_stoploss = [r for r in scanner_results if r.hit_stoploss]
        
        # Returns at different intervals
        returns_3min = [r.return_3min_pct for r in scanner_results if r.return_3min_pct is not None]
        returns_5min = [r.return_5min_pct for r in scanner_results if r.return_5min_pct is not None]
        returns_15min = [r.return_15min_pct for r in scanner_results if r.return_15min_pct is not None]
        returns_30min = [r.return_30min_pct for r in scanner_results if r.return_30min_pct is not None]
        
        # Max profit/loss
        max_profits = [r.max_profit_pct for r in scanner_results if r.max_profit_pct is not None]
        max_losses = [r.max_loss_pct for r in scanner_results if r.max_loss_pct is not None]
        
        print(f"\n📊 OVERVIEW:")
        print(f"   Total Triggers: {total_triggers}")
        print(f"   Date Range: {min(r.backtest_date for r in scanner_results).date()} to {max(r.backtest_date for r in scanner_results).date()}")
        
        print(f"\n✅ SUCCESS METRICS:")
        print(f"   Success Rate (3min positive): {len(successful)}/{total_triggers} ({len(successful)/total_triggers*100:.1f}%)")
        print(f"   Hit 1% Target: {len(hit_1pct)}/{total_triggers} ({len(hit_1pct)/total_triggers*100:.1f}%)")
        print(f"   Hit 2% Target: {len(hit_2pct)}/{total_triggers} ({len(hit_2pct)/total_triggers*100:.1f}%)")
        print(f"   Hit Stop Loss (-1%): {len(hit_stoploss)}/{total_triggers} ({len(hit_stoploss)/total_triggers*100:.1f}%)")
        
        print(f"\n📈 AVERAGE RETURNS:")
        if returns_3min:
            print(f"   3 minutes:  {sum(returns_3min)/len(returns_3min):+.2f}% ⭐ (NEW!)")
        if returns_5min:
            print(f"   5 minutes:  {sum(returns_5min)/len(returns_5min):+.2f}%")
        if returns_15min:
            print(f"   15 minutes: {sum(returns_15min)/len(returns_15min):+.2f}%")
        if returns_30min:
            print(f"   30 minutes: {sum(returns_30min)/len(returns_30min):+.2f}%")
        
        print(f"\n🎯 EXTREMES:")
        if max_profits:
            print(f"   Best Trade (Max Profit): {max(max_profits):+.2f}%")
        if max_losses:
            print(f"   Worst Trade (Max Loss):  {min(max_losses):+.2f}%")
        
        print(f"\n📋 ALL TRADES (sorted by 3min return):")
        sorted_results = sorted(scanner_results, 
                               key=lambda x: x.return_3min_pct if x.return_3min_pct else -999, 
                               reverse=True)
        
        for i, r in enumerate(sorted_results, 1):
            ret_3min = r.return_3min_pct if r.return_3min_pct else 0
            ret_5min = r.return_5min_pct if r.return_5min_pct else 0
            ret_15min = r.return_15min_pct if r.return_15min_pct else 0
            ret_30min = r.return_30min_pct if r.return_30min_pct else 0
            max_profit = r.max_profit_pct if r.max_profit_pct else 0
            trigger_time = r.trigger_time.strftime('%H:%M') if r.trigger_time else 'N/A'
            trigger_price = r.trigger_price if r.trigger_price else 0
            
            print(f"\n   Trade #{i}:")
            print(f"      Date: {r.backtest_date.date()} at {trigger_time}")
            print(f"      Trigger Price: ₹{trigger_price:.2f}")
            print(f"      Returns: 3min: {ret_3min:+6.2f}% | 5min: {ret_5min:+6.2f}% | 15min: {ret_15min:+6.2f}% | 30min: {ret_30min:+6.2f}%")
            print(f"      Max Profit: {max_profit:+6.2f}%")
            print(f"      Success: {'✅ YES' if r.was_successful else '❌ NO'}")
        
        # Show trigger times distribution
        print(f"\n⏰ TRIGGER TIME DISTRIBUTION:")
        trigger_hours = {}
        for r in scanner_results:
            if r.trigger_time:
                hour = r.trigger_time.hour
                trigger_hours[hour] = trigger_hours.get(hour, 0) + 1
        
        for hour in sorted(trigger_hours.keys()):
            count = trigger_hours[hour]
            bar = '█' * (count * 2)
            print(f"   {hour:02d}:00 - {hour:02d}:59: {bar} ({count})")
    
    # Cleanup
    r.delete('temp_cdsl_watchlist')
    db.close()
    
    print_header("BACKTEST COMPLETE")
    
    print("✅ Test completed successfully!")
    print("\n📝 Key Improvements Demonstrated:")
    print("  ✓ Minute-by-minute checking (not every 30 minutes)")
    print("  ✓ 3-minute interval returns for fast scalping")
    print("  ✓ All triggers captured (with 30min gap)")
    print("  ✓ Exact trigger times and prices recorded")
    
    print("\n")


if __name__ == "__main__":
    main()

