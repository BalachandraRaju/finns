#!/usr/bin/env python3
"""
Backfill script to fetch latest data for all watchlist stocks.
This script:
1. Gets all stocks from watchlist
2. Fetches today's intraday data from market open to current time
3. Saves to database
4. Shows progress and summary
"""

import sys
sys.path.insert(0, 'data-fetch')

from dhan_live_data_service import dhan_live_data_service
from dhan_historical_client import DhanHistoricalClient
from app.crud import get_watchlist_details
from app.db import SessionLocal
from app.models import Candle
from datetime import datetime, timedelta
import pytz
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_market_hours():
    """Get today's market hours in IST."""
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    return market_start, market_end, now

def backfill_all_stocks():
    """Backfill all watchlist stocks with today's data."""
    
    print("\n" + "="*80)
    print("🔄 BACKFILL ALL STOCKS - FETCHING LATEST DATA")
    print("="*80)
    
    # Check market hours
    market_start, market_end, now = get_market_hours()
    
    print(f"\n📅 Current Time: {now.strftime('%Y-%m-%d %H:%M:%S IST')}")
    print(f"📊 Market Hours: {market_start.strftime('%H:%M')} - {market_end.strftime('%H:%M')}")
    
    if now < market_start:
        print(f"⚠️  Market hasn't opened yet. Opens at {market_start.strftime('%H:%M')}")
        return
    
    # Get all watchlist stocks
    print("\n📋 Getting watchlist stocks...")
    try:
        watchlist = get_watchlist_details()
        stocks = []
        
        for stock in watchlist:
            if hasattr(stock, 'instrument_key'):
                instrument_key = stock.instrument_key
                symbol = stock.symbol
            elif isinstance(stock, dict):
                instrument_key = stock.get('instrument_key', '')
                symbol = stock.get('symbol', '')
            else:
                continue
            
            if instrument_key.startswith('DHAN_'):
                security_id = instrument_key.replace('DHAN_', '')
                stocks.append({
                    'instrument_key': instrument_key,
                    'symbol': symbol,
                    'security_id': security_id
                })
        
        print(f"✅ Found {len(stocks)} stocks in watchlist")
        
    except Exception as e:
        logger.error(f"❌ Error getting watchlist: {e}")
        return
    
    if not stocks:
        print("⚠️  No stocks found in watchlist")
        return
    
    # Initialize Dhan client
    print("\n🔌 Initializing Dhan API client...")
    client = DhanHistoricalClient()
    
    # Backfill each stock
    print(f"\n🚀 Starting backfill for {len(stocks)} stocks...")
    print("="*80)
    
    success_count = 0
    error_count = 0
    total_candles = 0
    
    db = SessionLocal()
    
    try:
        for i, stock in enumerate(stocks, 1):
            symbol = stock['symbol']
            security_id = stock['security_id']
            instrument_key = stock['instrument_key']
            
            print(f"\n[{i}/{len(stocks)}] 📊 {symbol} (ID: {security_id})")
            
            try:
                # Fetch today's data from market open to now
                from_date = market_start
                to_date = now
                
                candles = client.get_intraday_data(
                    security_id=int(security_id),
                    from_date=from_date,
                    to_date=to_date,
                    interval='1',
                    exchange_segment='NSE_EQ',
                    instrument='EQUITY',
                    stock_symbol=symbol
                )
                
                if not candles:
                    print(f"  ⚠️  No data received")
                    error_count += 1
                    continue
                
                # Save candles to database
                saved_count = 0
                updated_count = 0
                
                for candle in candles:
                    timestamp = candle['timestamp']
                    
                    # Check if candle already exists
                    existing = db.query(Candle).filter(
                        Candle.instrument_key == instrument_key,
                        Candle.interval == '1minute',
                        Candle.timestamp == timestamp
                    ).first()
                    
                    if existing:
                        # Update existing candle
                        existing.open = candle['open']
                        existing.high = candle['high']
                        existing.low = candle['low']
                        existing.close = candle['close']
                        existing.volume = candle['volume']
                        updated_count += 1
                    else:
                        # Insert new candle
                        new_candle = Candle(
                            instrument_key=instrument_key,
                            interval='1minute',
                            timestamp=timestamp,
                            open=candle['open'],
                            high=candle['high'],
                            low=candle['low'],
                            close=candle['close'],
                            volume=candle['volume']
                        )
                        db.add(new_candle)
                        saved_count += 1
                
                db.commit()
                
                total_candles += len(candles)
                success_count += 1
                
                latest_price = candles[-1]['close']
                latest_time = candles[-1]['timestamp'].strftime('%H:%M')
                
                print(f"  ✅ Saved {saved_count} new, updated {updated_count} existing candles")
                print(f"  💰 Latest: ₹{latest_price:.2f} at {latest_time}")
                
            except Exception as e:
                logger.error(f"  ❌ Error: {e}")
                error_count += 1
                db.rollback()
                continue
    
    finally:
        db.close()
    
    # Summary
    print("\n" + "="*80)
    print("📊 BACKFILL SUMMARY")
    print("="*80)
    print(f"✅ Success: {success_count} stocks")
    print(f"❌ Errors: {error_count} stocks")
    print(f"📈 Total candles processed: {total_candles}")
    print(f"⏱️  Completed at: {datetime.now().strftime('%H:%M:%S')}")
    print("="*80)
    
    if success_count > 0:
        print("\n🎉 Backfill complete! Database updated with latest data.")
        print("💡 Charts will now show data till current time.")
        print("🔔 Alerts will run with latest data on next scheduler cycle.")
    
    return success_count, error_count, total_candles

if __name__ == "__main__":
    try:
        backfill_all_stocks()
    except KeyboardInterrupt:
        print("\n\n⚠️  Backfill interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

