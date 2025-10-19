#!/usr/bin/env python3
"""
Simple CDSL Backtest Test
"""
import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'pkscreener-integration')

from app.db import get_db
from sqlalchemy import text
from datetime import datetime, timedelta
import json
import redis

print("="*80)
print("CDSL BACKTEST TEST")
print("="*80)

# Get CDSL from watchlist
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
watchlist_json = r.get('watchlist')

if not watchlist_json:
    print("❌ No watchlist in Redis")
    sys.exit(1)

watchlist = json.loads(watchlist_json)
cdsl = next((s for s in watchlist if s.get('symbol') == 'CDSL'), None)

if not cdsl:
    print("❌ CDSL not in watchlist")
    sys.exit(1)

print(f"\n✅ Found CDSL:")
print(f"   Symbol: {cdsl['symbol']}")
print(f"   Instrument Key: {cdsl['instrument_key']}")

# Check data
db = next(get_db())
result = db.execute(text('''
    SELECT COUNT(*), MIN(timestamp), MAX(timestamp)
    FROM candles 
    WHERE instrument_key = :key AND interval = '1'
'''), {'key': cdsl['instrument_key']}).fetchone()

print(f"\n📊 Data Available:")
print(f"   Total Candles: {result[0]:,}")
print(f"   First: {result[1]}")
print(f"   Last: {result[2]}")

if result[0] == 0:
    print("\n❌ No data available - run backfill first")
    db.close()
    sys.exit(1)

# Run backtest
print(f"\n🚀 Running backtest...")

from backtest_engine import BacktestEngine

engine = BacktestEngine(db)
engine.stocks = [cdsl]  # Override with just CDSL

end_date = datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)
start_date = end_date - timedelta(days=60)

print(f"   Period: {start_date.date()} to {end_date.date()}")
print(f"   Scanners: #1, #12")

results = engine.run_backtest(
    scanner_ids=[1, 12],
    start_date=start_date,
    end_date=end_date,
    max_stocks=1
)

print(f"\n📊 RESULTS:")
print("="*80)

for scanner_id in [1, 12]:
    scanner_results = results[scanner_id]
    print(f"\nScanner #{scanner_id}: {len(scanner_results)} triggers")
    
    if scanner_results:
        for i, r in enumerate(scanner_results[:5], 1):
            ret_3min = r.return_3min_pct if r.return_3min_pct else 0
            ret_30min = r.return_30min_pct if r.return_30min_pct else 0
            print(f"  {i}. {r.backtest_date.date()} at {r.trigger_time.strftime('%H:%M') if r.trigger_time else 'N/A'}")
            print(f"     Price: ₹{r.trigger_price:.2f} | 3min: {ret_3min:+.2f}% | 30min: {ret_30min:+.2f}%")

db.close()
print("\n✅ Test complete!")

