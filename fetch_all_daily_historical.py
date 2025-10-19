#!/usr/bin/env python3
"""
Fetch 5 years of daily historical data for all stocks in watchlist
Store in MongoDB: trading_data.daily_candles
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(__file__))

# Import the fetcher
import importlib.util
spec = importlib.util.spec_from_file_location("fetch_daily_historical", "data-fetch/fetch_daily_historical.py")
fetch_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch_module)

DailyHistoricalFetcher = fetch_module.DailyHistoricalFetcher

from app.crud import get_watchlist_details
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_security_id(instrument_key: str) -> str:
    """Extract security ID from instrument key"""
    if instrument_key.startswith('DHAN_'):
        return instrument_key.replace('DHAN_', '')
    # For NSE_EQ format, we'll need to look it up or skip
    return None


def fetch_all_stocks():
    """Fetch daily historical data for all stocks"""
    logger.info("="*80)
    logger.info("FETCHING 5 YEARS DAILY HISTORICAL DATA FOR ALL STOCKS")
    logger.info("="*80)
    
    # Get watchlist
    watchlist = get_watchlist_details()
    logger.info(f"\nTotal stocks in watchlist: {len(watchlist)}")
    
    # Filter stocks with DHAN_ prefix (have security IDs)
    dhan_stocks = [s for s in watchlist if s.instrument_key.startswith('DHAN_')]
    logger.info(f"Stocks with Dhan security IDs: {len(dhan_stocks)}")
    
    fetcher = DailyHistoricalFetcher()
    
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    for idx, stock in enumerate(dhan_stocks, 1):
        security_id = extract_security_id(stock.instrument_key)
        
        if not security_id:
            logger.warning(f"[{idx}/{len(dhan_stocks)}] Skipping {stock.symbol} - no security ID")
            skipped_count += 1
            continue
        
        logger.info(f"\n[{idx}/{len(dhan_stocks)}] Fetching {stock.symbol} (security_id: {security_id})...")
        
        try:
            result = fetcher.fetch_daily_data(
                security_id=security_id,
                instrument_key=stock.instrument_key,
                symbol=stock.symbol,
                years=5
            )
            
            if result:
                success_count += 1
                logger.info(f"  ✅ Success")
            else:
                failed_count += 1
                logger.error(f"  ❌ Failed")
            
            # Rate limiting: Dhan allows 100 requests per minute
            # Sleep for 0.6 seconds between requests (100 requests/min = 1 request per 0.6s)
            time.sleep(0.6)
            
        except Exception as e:
            logger.error(f"  ❌ Error: {e}")
            failed_count += 1
            time.sleep(1)  # Longer sleep on error
    
    logger.info("\n" + "="*80)
    logger.info("FETCH COMPLETE")
    logger.info("="*80)
    logger.info(f"Total stocks: {len(dhan_stocks)}")
    logger.info(f"✅ Success: {success_count}")
    logger.info(f"❌ Failed: {failed_count}")
    logger.info(f"⏭️  Skipped: {skipped_count}")
    
    # Show database statistics
    from pymongo import MongoClient
    mongo_client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
    mongo_db = mongo_client[os.getenv('MONGO_DB', 'trading_data')]
    
    total_candles = mongo_db.daily_candles.count_documents({})
    unique_symbols = len(mongo_db.daily_candles.distinct('symbol'))
    
    logger.info(f"\n📊 MongoDB Statistics:")
    logger.info(f"   Total daily candles: {total_candles:,}")
    logger.info(f"   Unique symbols: {unique_symbols}")
    
    # Show sample data
    logger.info(f"\n📈 Sample data (latest candles):")
    for candle in mongo_db.daily_candles.find().sort('date', -1).limit(5):
        logger.info(f"   {candle['symbol']:12} {candle['date']}: Close={candle['close']:.2f} Volume={candle['volume']:,}")
    
    mongo_client.close()


if __name__ == '__main__':
    fetch_all_stocks()

