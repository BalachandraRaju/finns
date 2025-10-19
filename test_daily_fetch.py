#!/usr/bin/env python3
"""
Test daily historical data fetching for a few stocks
"""
import sys
import os
sys.path.insert(0, '.')
sys.path.insert(0, 'data-fetch')

# Import from the correct path
import importlib.util
spec = importlib.util.spec_from_file_location("fetch_daily_historical", "data-fetch/fetch_daily_historical.py")
fetch_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch_module)
DailyHistoricalFetcher = fetch_module.DailyHistoricalFetcher

from app.crud import get_watchlist_details

def test_fetch():
    """Test fetching daily data for first 5 stocks"""
    print("\n" + "="*80)
    print("TESTING DAILY HISTORICAL DATA FETCH")
    print("="*80)
    
    fetcher = DailyHistoricalFetcher()
    
    # Get first 5 stocks from watchlist
    watchlist = get_watchlist_details()
    test_stocks = watchlist[:5]
    
    print(f"\nTesting with {len(test_stocks)} stocks...")
    
    for idx, stock in enumerate(test_stocks, 1):
        security_id = stock.instrument_key.replace('DHAN_', '')
        
        print(f"\n[{idx}/{len(test_stocks)}] Fetching {stock.symbol}...")
        
        success = fetcher.fetch_daily_data(
            security_id=security_id,
            instrument_key=stock.instrument_key,
            symbol=stock.symbol,
            years=5
        )
        
        if success:
            # Get stats
            stats = fetcher.daily_stats.find_one({'instrument_key': stock.instrument_key})
            if stats:
                print(f"  ✅ Success!")
                print(f"  Total days: {stats['total_days']}")
                print(f"  Avg daily volume: {stats['avg_daily_volume']:,.0f}")
                print(f"  Avg 20-day volume: {stats['avg_volume_20d']:,.0f}")
        else:
            print(f"  ❌ Failed")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == '__main__':
    test_fetch()

