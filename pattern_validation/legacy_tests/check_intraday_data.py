#!/usr/bin/env python3
"""
Script to check what intraday data is available in the database for today.
"""

import sys
import os
import datetime
from logzero import logger

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal
from app.models import Candle
from sqlalchemy import func, desc

def check_todays_intraday_data():
    """Check what 1-minute data is available for today."""
    db_session = SessionLocal()
    try:
        today = datetime.date.today()
        logger.info(f"Checking 1-minute data for today: {today}")
        
        # Get all 1-minute candles for today
        query = db_session.query(Candle).filter(
            Candle.interval == "1minute",
            func.date(Candle.timestamp) == today
        ).order_by(desc(Candle.timestamp))
        
        candles = query.all()
        
        if not candles:
            logger.info("❌ No 1-minute data found for today")
            return
        
        logger.info(f"✅ Found {len(candles)} 1-minute candles for today")
        
        # Group by instrument
        by_instrument = {}
        for candle in candles:
            if candle.instrument_key not in by_instrument:
                by_instrument[candle.instrument_key] = []
            by_instrument[candle.instrument_key].append(candle)
        
        logger.info("-" * 80)
        for instrument_key, instrument_candles in by_instrument.items():
            logger.info(f"Instrument: {instrument_key}")
            logger.info(f"  Total candles: {len(instrument_candles)}")
            
            # Show first and last candle times
            first_candle = max(instrument_candles, key=lambda c: c.timestamp)
            last_candle = min(instrument_candles, key=lambda c: c.timestamp)
            
            logger.info(f"  Latest candle: {first_candle.timestamp} (O:{first_candle.open}, H:{first_candle.high}, L:{first_candle.low}, C:{first_candle.close})")
            logger.info(f"  Earliest candle: {last_candle.timestamp}")
            logger.info("-" * 40)
            
    except Exception as e:
        logger.error(f"Error checking today's data: {e}")
    finally:
        db_session.close()

def check_recent_intraday_data():
    """Check the most recent 1-minute data regardless of date."""
    db_session = SessionLocal()
    try:
        logger.info("Checking most recent 1-minute data...")
        
        # Get the most recent 1-minute candles
        query = db_session.query(Candle).filter(
            Candle.interval == "1minute"
        ).order_by(desc(Candle.timestamp)).limit(20)
        
        candles = query.all()
        
        if not candles:
            logger.info("❌ No 1-minute data found at all")
            return
        
        logger.info(f"✅ Found recent 1-minute candles")
        logger.info("-" * 80)
        
        for candle in candles:
            logger.info(f"{candle.instrument_key} | {candle.timestamp} | O:{candle.open} H:{candle.high} L:{candle.low} C:{candle.close}")
            
    except Exception as e:
        logger.error(f"Error checking recent data: {e}")
    finally:
        db_session.close()

def main():
    """Main function."""
    logger.info("🔍 Checking intraday data availability...")
    
    check_todays_intraday_data()
    logger.info("\n" + "="*80 + "\n")
    check_recent_intraday_data()

if __name__ == "__main__":
    main()
