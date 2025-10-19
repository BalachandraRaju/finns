#!/usr/bin/env python3
"""
Test fetching 5 years of daily historical data from Dhan API
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Import the fetcher
import importlib.util
spec = importlib.util.spec_from_file_location("fetch_daily_historical", "data-fetch/fetch_daily_historical.py")
fetch_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch_module)

DailyHistoricalFetcher = fetch_module.DailyHistoricalFetcher

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_single_stock():
    """Test with a single stock first"""
    logger.info("="*80)
    logger.info("TESTING DAILY HISTORICAL DATA FETCH - SINGLE STOCK")
    logger.info("="*80)
    
    fetcher = DailyHistoricalFetcher()
    
    # Test with RELIANCE (security_id: 1333)
    logger.info("\nTesting with RELIANCE (security_id: 1333)...")
    result = fetcher.fetch_daily_data('1333', 'DHAN_1333', 'RELIANCE', years=5)
    
    if result:
        logger.info("✅ Successfully fetched and stored data")
        
        # Show sample data
        from pymongo import MongoClient
        mongo_client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
        mongo_db = mongo_client[os.getenv('MONGO_DB', 'trading_data')]
        
        count = mongo_db.daily_candles.count_documents({'symbol': 'RELIANCE'})
        logger.info(f"\nTotal candles stored for RELIANCE: {count}")
        
        # Show latest 5 candles
        logger.info("\nLatest 5 candles:")
        for candle in mongo_db.daily_candles.find({'symbol': 'RELIANCE'}).sort('date', -1).limit(5):
            logger.info(f"  {candle['date']}: O={candle['open']:.2f} H={candle['high']:.2f} L={candle['low']:.2f} C={candle['close']:.2f} V={candle['volume']:,}")
        
        mongo_client.close()
    else:
        logger.error("❌ Failed to fetch data")
    
    logger.info("\n" + "="*80)

if __name__ == '__main__':
    test_single_stock()

