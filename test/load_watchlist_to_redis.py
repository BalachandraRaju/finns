#!/usr/bin/env python3
"""
Load watchlist from database to Redis
"""
import sys
sys.path.insert(0, '.')

from app import crud
import redis
import json

print("="*80)
print("Loading Watchlist to Redis")
print("="*80)

# Get watchlist from database
print("\n1. Fetching watchlist from database...")
watchlist = crud.get_watchlist_details()

if not watchlist:
    print("❌ No watchlist found in database")
    sys.exit(1)

print(f"✅ Found {len(watchlist)} stocks in database")

# Convert to dict format
watchlist_data = []
for stock in watchlist:
    watchlist_data.append({
        'symbol': stock.symbol,
        'instrument_key': stock.instrument_key,
        'company_name': stock.company_name,
        'exchange': getattr(stock, 'exchange', 'NSE')
    })

# Save to Redis
print("\n2. Saving to Redis...")
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
r.set('watchlist', json.dumps(watchlist_data))

print(f"✅ Loaded {len(watchlist_data)} stocks into Redis watchlist")

# Check if CDSL is in the list
print("\n3. Checking for CDSL...")
cdsl = next((s for s in watchlist_data if s['symbol'] == 'CDSL'), None)

if cdsl:
    print(f"✅ CDSL found!")
    print(f"   Symbol: {cdsl['symbol']}")
    print(f"   Instrument Key: {cdsl['instrument_key']}")
    print(f"   Company: {cdsl['company_name']}")
    print(f"   Exchange: {cdsl['exchange']}")
else:
    print("⚠️  CDSL not found in watchlist")
    print("\nStocks with 'CD' in symbol:")
    cd_stocks = [s for s in watchlist_data if 'CD' in s['symbol']]
    for s in cd_stocks[:10]:
        print(f"  - {s['symbol']:15} {s['instrument_key']:20} {s['company_name']}")

print("\n" + "="*80)
print("✅ Watchlist loaded successfully!")
print("="*80)
print("\nYou can now run: python3 run_cdsl_backtest.py")

