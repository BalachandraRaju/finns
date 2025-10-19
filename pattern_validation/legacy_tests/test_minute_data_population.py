#!/usr/bin/env python3
"""
Test script to populate 1-minute data for watchlist stocks.
This script can be run to pre-populate the database with 2 months of 1-minute data.
"""

import sys
import os
import datetime
from logzero import logger

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import charts, crud
from app.db import Base, engine

def test_single_stock():
    """Test data population for a single stock."""
    # Use TCS as an example
    instrument_key = "NSE_EQ|INE467B01029"  # TCS
    
    logger.info(f"Testing 1-minute data population for {instrument_key}")
    
    try:
        charts.populate_minute_data_for_stock(instrument_key)
        logger.info("✅ Single stock test completed successfully")
    except Exception as e:
        logger.error(f"❌ Single stock test failed: {e}")

def test_watchlist_population():
    """Test data population for all watchlist stocks."""
    logger.info("Testing 1-minute data population for all watchlist stocks")
    
    try:
        charts.populate_minute_data_for_watchlist()
        logger.info("✅ Watchlist population test completed successfully")
    except Exception as e:
        logger.error(f"❌ Watchlist population test failed: {e}")

def check_data_availability():
    """Check how much 1-minute data is available in the database."""
    from app.db import SessionLocal
    from app.models import Candle
    
    db_session = SessionLocal()
    try:
        # Count 1-minute candles by instrument
        from sqlalchemy import func
        query = db_session.query(
            Candle.instrument_key,
            func.min(Candle.timestamp).label('earliest_date'),
            func.max(Candle.timestamp).label('latest_date'),
            func.count(Candle.id).label('candle_count')
        ).filter(
            Candle.interval == "1minute"
        ).group_by(Candle.instrument_key)
        
        results = query.all()
        
        if not results:
            logger.info("No 1-minute data found in database")
            return
        
        logger.info("1-minute data availability:")
        logger.info("-" * 80)
        for result in results:
            # Get stock symbol for display
            stock_info = crud.get_stock_by_instrument_key(result.instrument_key)
            symbol = stock_info['symbol'] if stock_info else result.instrument_key
            
            logger.info(f"Stock: {symbol}")
            logger.info(f"  Instrument Key: {result.instrument_key}")
            logger.info(f"  Earliest Data: {result.earliest_date}")
            logger.info(f"  Latest Data: {result.latest_date}")
            logger.info(f"  Total Candles: {result.candle_count}")
            logger.info("-" * 40)
            
    except Exception as e:
        logger.error(f"Error checking data availability: {e}")
    finally:
        db_session.close()

def main():
    """Main function to run tests."""
    logger.info("🚀 Starting 1-minute data population tests")
    logger.info("=" * 60)
    
    # Ensure database tables exist
    Base.metadata.create_all(bind=engine)
    
    # Check current data availability
    logger.info("📊 Checking current data availability...")
    check_data_availability()
    
    # Test single stock population
    logger.info("\n🔍 Testing single stock population...")
    test_single_stock()
    
    # Check data availability after single stock test
    logger.info("\n📊 Checking data availability after single stock test...")
    check_data_availability()
    
    # Uncomment the following lines to test full watchlist population
    # logger.info("\n🔍 Testing full watchlist population...")
    # test_watchlist_population()
    
    # logger.info("\n📊 Final data availability check...")
    # check_data_availability()
    
    logger.info("\n✅ All tests completed!")

if __name__ == "__main__":
    main()
