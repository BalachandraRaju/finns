"""
Test volume-only scanner to see how many stocks have high volume
"""
import sys
import os
from datetime import datetime, timedelta
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import get_db
from app.models import Candle
from app.crud import get_watchlist_details
from sqlalchemy import and_
import importlib.util

# Import daily data service
spec = importlib.util.spec_from_file_location("daily_data_service", "pkscreener-integration/daily_data_service.py")
daily_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(daily_module)

spec2 = importlib.util.spec_from_file_location("technical_indicators", "pkscreener-integration/technical_indicators.py")
ti_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(ti_module)

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_volume_only():
    """Test how many stocks pass volume filter only"""
    
    db = next(get_db())
    daily_service = daily_module.get_daily_data_service()
    ti = ti_module.TechnicalIndicators()
    
    # Get watchlist
    stocks = get_watchlist_details()
    logger.info(f"Testing {len(stocks)} stocks")
    
    # Test yesterday at 10 AM
    test_date = datetime.now() - timedelta(days=1)
    test_date = test_date.replace(hour=10, minute=0, second=0, microsecond=0)
    
    logger.info(f"Test Date: {test_date.strftime('%Y-%m-%d %H:%M')}")
    logger.info("")
    
    volume_pass_count = 0
    volume_pass_stocks = []
    
    for stock in stocks[:50]:  # Test first 50 stocks
        # Get candles around test time
        start_time = test_date - timedelta(minutes=30)
        end_time = test_date + timedelta(minutes=5)
        
        candles = db.query(Candle).filter(
            and_(
                Candle.instrument_key == stock.instrument_key,
                Candle.interval == '1minute',
                Candle.timestamp >= start_time,
                Candle.timestamp <= end_time
            )
        ).order_by(Candle.timestamp.desc()).limit(50).all()
        
        if not candles or len(candles) < 10:
            continue
        
        # Get latest candle volume
        recent_volume = candles[0].volume
        
        # Calculate volume ratio
        volume_ratio = ti.calculate_intraday_volume_ratio(
            recent_volume,
            stock.instrument_key,
            daily_service
        )
        
        if volume_ratio >= 1.5:
            volume_pass_count += 1
            volume_pass_stocks.append({
                'symbol': stock.symbol,
                'volume_ratio': volume_ratio,
                'volume': recent_volume
            })
    
    logger.info("="*80)
    logger.info(f"VOLUME FILTER RESULTS (1.5x threshold)")
    logger.info("="*80)
    logger.info(f"Stocks Tested: 50")
    logger.info(f"Stocks Passing Volume Filter: {volume_pass_count}")
    logger.info(f"Pass Rate: {volume_pass_count/50*100:.1f}%")
    logger.info("")
    
    if volume_pass_stocks:
        logger.info("Top 10 stocks by volume ratio:")
        sorted_stocks = sorted(volume_pass_stocks, key=lambda x: x['volume_ratio'], reverse=True)
        for i, stock in enumerate(sorted_stocks[:10], 1):
            logger.info(f"  {i}. {stock['symbol']}: {stock['volume_ratio']:.2f}x (Volume: {stock['volume']:,})")
    
    db.close()


if __name__ == "__main__":
    test_volume_only()

