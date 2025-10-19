#!/usr/bin/env python3
"""
Calculate daily volume averages from existing 1-minute intraday data
Store in MongoDB for use by intraday scanners

This is BETTER than fetching daily data because:
1. We already have the data
2. More accurate (sum of actual intraday volumes)
3. No API rate limits
"""
import sys
sys.path.insert(0, '.')

from datetime import datetime, timedelta
from app.db import get_db
from app.models import Candle
from sqlalchemy import func, and_
from pymongo import MongoClient, ASCENDING
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
MONGO_DB = os.getenv('MONGO_DB', 'trading_data')


def calculate_daily_volumes():
    """Calculate daily volume from 1-minute candles"""
    logger.info("="*80)
    logger.info("CALCULATING DAILY VOLUMES FROM INTRADAY DATA")
    logger.info("="*80)
    
    # Connect to databases
    db = next(get_db())
    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client[MONGO_DB]
    daily_stats = mongo_db['daily_stats']
    
    # Create index
    daily_stats.create_index([('instrument_key', ASCENDING)], unique=True)
    
    # Get all unique instruments
    instruments = db.query(Candle.instrument_key).filter(
        Candle.interval == '1minute'
    ).distinct().all()

    logger.info(f"\nFound {len(instruments)} instruments with 1-minute data")
    
    for idx, (instrument_key,) in enumerate(instruments, 1):
        logger.info(f"\n[{idx}/{len(instruments)}] Processing {instrument_key}...")
        
        # Get all dates for this instrument
        dates = db.query(
            func.date(Candle.timestamp).label('date'),
            func.sum(Candle.volume).label('total_volume'),
            func.count(Candle.id).label('candle_count')
        ).filter(
            and_(
                Candle.instrument_key == instrument_key,
                Candle.interval == '1minute'
            )
        ).group_by(func.date(Candle.timestamp)).order_by(func.date(Candle.timestamp).desc()).all()
        
        if not dates:
            logger.warning(f"  No data for {instrument_key}")
            continue
        
        # Calculate statistics
        daily_volumes = [d.total_volume for d in dates if d.total_volume > 0]
        
        if not daily_volumes:
            logger.warning(f"  No volume data for {instrument_key}")
            continue
        
        # Calculate averages
        avg_daily_volume = sum(daily_volumes) / len(daily_volumes)
        avg_volume_20d = sum(daily_volumes[:20]) / min(20, len(daily_volumes))
        avg_volume_50d = sum(daily_volumes[:50]) / min(50, len(daily_volumes))
        
        # Get symbol from watchlist
        from app.crud import get_watchlist_details
        watchlist = get_watchlist_details()
        symbol = next((s.symbol for s in watchlist if s.instrument_key == instrument_key), instrument_key)
        
        # Store in MongoDB
        stats = {
            'instrument_key': instrument_key,
            'symbol': symbol,
            'total_days': len(dates),
            'avg_daily_volume': avg_daily_volume,
            'max_daily_volume': max(daily_volumes),
            'min_daily_volume': min(daily_volumes),
            'avg_volume_20d': avg_volume_20d,
            'avg_volume_50d': avg_volume_50d,
            'last_updated': datetime.now(),
            'data_source': 'calculated_from_1min_candles'
        }
        
        daily_stats.update_one(
            {'instrument_key': instrument_key},
            {'$set': stats},
            upsert=True
        )
        
        logger.info(f"  ✅ {symbol}")
        logger.info(f"     Days: {len(dates)}")
        logger.info(f"     Avg daily volume: {avg_daily_volume:,.0f}")
        logger.info(f"     Avg 20-day volume: {avg_volume_20d:,.0f}")
    
    logger.info("\n" + "="*80)
    logger.info("DAILY VOLUME CALCULATION COMPLETE")
    logger.info("="*80)
    logger.info(f"Processed {len(instruments)} instruments")
    
    # Show sample stats
    logger.info("\nSample statistics:")
    for stat in daily_stats.find().limit(5):
        logger.info(f"  {stat['symbol']}: Avg daily volume = {stat['avg_daily_volume']:,.0f}")
    
    db.close()
    mongo_client.close()


if __name__ == '__main__':
    calculate_daily_volumes()

