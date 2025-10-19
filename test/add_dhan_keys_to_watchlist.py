#!/usr/bin/env python3
"""
Add Dhan instrument keys to watchlist for all F&O stocks.
This script maps stock symbols to Dhan security IDs and adds them to the watchlist.
"""

import sys
import os

# Add paths
sys.path.insert(0, '/Users/balachandra.raju/projects/finns')
sys.path.insert(0, '/Users/balachandra.raju/projects/finns/data-fetch')

from app import crud, models
from app.db import redis_client
from dhan_instruments import dhan_instruments
from logzero import logger
from datetime import datetime

def load_fo_symbols():
    """Load F&O stock symbols from file."""
    try:
        with open('nse_fo_stock_symbols.txt', 'r') as f:
            content = f.read()
            # Split by comma and clean up
            symbols = [s.strip().strip('"').strip("'") for s in content.split(',')]
            # Filter out empty strings, test symbols, and indices
            symbols = [
                s for s in symbols 
                if s and 'NSETEST' not in s and s not in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY']
            ]
            return symbols
    except Exception as e:
        logger.error(f"❌ Error loading F&O symbols: {e}")
        return []

def add_dhan_stocks_to_watchlist(limit=None):
    """
    Add Dhan instrument keys to watchlist for F&O stocks.
    
    Args:
        limit: Maximum number of stocks to add (None = all stocks)
    """
    print("=" * 80)
    print("📊 ADDING DHAN INSTRUMENT KEYS TO WATCHLIST")
    print("=" * 80)
    
    # Load F&O symbols
    print("\n1️⃣ Loading F&O stock symbols...")
    symbols = load_fo_symbols()
    print(f"✅ Loaded {len(symbols)} F&O symbols")
    
    if limit:
        symbols = symbols[:limit]
        print(f"⚠️ Limiting to first {limit} stocks for testing")
    
    # Get Dhan security IDs
    print("\n2️⃣ Mapping symbols to Dhan security IDs...")
    mapped_stocks = []
    skipped_stocks = []
    
    for symbol in symbols:
        security_id = dhan_instruments.get_security_id(symbol)
        if security_id:
            instrument_key = f"DHAN_{security_id}"
            mapped_stocks.append({
                'symbol': symbol,
                'security_id': security_id,
                'instrument_key': instrument_key
            })
        else:
            skipped_stocks.append(symbol)
    
    print(f"✅ Mapped {len(mapped_stocks)} stocks")
    print(f"⚠️ Skipped {len(skipped_stocks)} stocks (no security ID found)")
    
    if skipped_stocks[:5]:
        print(f"   Skipped examples: {', '.join(skipped_stocks[:5])}")
    
    # Add to watchlist using Redis
    print("\n3️⃣ Adding stocks to watchlist...")
    added_count = 0
    already_exists_count = 0
    error_count = 0

    if not redis_client:
        print("❌ Redis not available, cannot add stocks to watchlist")
        return 0

    # Get existing watchlist symbols
    existing_symbols = redis_client.smembers("watchlist:symbols")

    for stock_info in mapped_stocks:
        try:
            symbol = stock_info['symbol']

            # Check if already in watchlist
            if symbol in existing_symbols:
                already_exists_count += 1
                continue

            # Prepare stock details for Redis
            stock_details = {
                'instrument_key': stock_info['instrument_key'],
                'company_name': symbol,  # Use symbol as company name for now
                'tags': 'F&O,Dhan',
                'trade_type': 'Neutral',
                'added_at': datetime.utcnow().isoformat()
            }

            # Add to Redis
            pipeline = redis_client.pipeline()
            pipeline.sadd("watchlist:symbols", symbol)
            pipeline.hset(f"watchlist:details:{symbol}", mapping=stock_details)
            pipeline.execute()

            added_count += 1

            if added_count % 10 == 0:
                print(f"   Added {added_count} stocks...")

        except Exception as e:
            error_count += 1
            logger.error(f"❌ Error adding {stock_info['symbol']}: {e}")
            continue

    print(f"\n✅ Successfully added {added_count} stocks to watchlist")
    print(f"⚠️ {already_exists_count} stocks already in watchlist")
    if error_count > 0:
        print(f"❌ {error_count} errors occurred")
    
    # Display summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"   Total F&O symbols: {len(symbols)}")
    print(f"   Successfully mapped: {len(mapped_stocks)}")
    print(f"   Added to watchlist: {added_count}")
    print(f"   Already in watchlist: {already_exists_count}")
    print(f"   Skipped (no security ID): {len(skipped_stocks)}")
    print(f"   Errors: {error_count}")
    print("=" * 80)
    
    return added_count

def verify_watchlist():
    """Verify watchlist has Dhan instrument keys."""
    print("\n" + "=" * 80)
    print("🔍 VERIFYING WATCHLIST")
    print("=" * 80)
    
    watchlist = crud.get_watchlist_details()
    
    dhan_stocks = [s for s in watchlist if s.instrument_key.startswith('DHAN_')]
    upstox_stocks = [s for s in watchlist if s.instrument_key.startswith('NSE_')]
    
    print(f"\nTotal stocks in watchlist: {len(watchlist)}")
    print(f"   Dhan stocks: {len(dhan_stocks)}")
    print(f"   Upstox stocks: {len(upstox_stocks)}")
    
    if dhan_stocks:
        print(f"\nFirst 5 Dhan stocks:")
        for i, stock in enumerate(dhan_stocks[:5], 1):
            print(f"   {i}. {stock.symbol} - {stock.instrument_key}")
    
    print("=" * 80)

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Add Dhan instrument keys to watchlist')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of stocks to add (for testing)')
    parser.add_argument('--verify-only', action='store_true', help='Only verify watchlist, do not add stocks')
    
    args = parser.parse_args()
    
    if args.verify_only:
        verify_watchlist()
        return 0
    
    # Add stocks
    added_count = add_dhan_stocks_to_watchlist(limit=args.limit)
    
    # Verify
    verify_watchlist()
    
    if added_count > 0:
        print("\n✅ SUCCESS! Dhan stocks added to watchlist")
        print("🌐 View watchlist at: http://localhost:8000/")
        return 0
    else:
        print("\n⚠️ No new stocks added (all may already exist)")
        return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

