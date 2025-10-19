"""
Diagnose why scanners are not generating alerts
Check volume ratios and other metrics
"""
import sys
import os
from datetime import datetime, timedelta
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pkscreener-integration'))

from app.db import get_db
from app.models import Candle
from sqlalchemy import and_
import importlib.util

# Import modules
spec = importlib.util.spec_from_file_location("daily_data_service", "pkscreener-integration/daily_data_service.py")
daily_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(daily_module)

spec2 = importlib.util.spec_from_file_location("scanner_strategies", "pkscreener-integration/scanner_strategies.py")
scanner_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(scanner_module)

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def diagnose():
    """Diagnose scanner issues"""
    
    db = next(get_db())
    
    # Initialize services
    daily_service = daily_module.get_daily_data_service()
    strategies = scanner_module.ScannerStrategies(daily_data_service=daily_service)
    
    # Test on a few stocks
    test_stocks = [
        {'symbol': 'RELIANCE', 'instrument_key': 'DHAN_2885'},
        {'symbol': 'TATASTEEL', 'instrument_key': 'DHAN_3499'},
        {'symbol': 'SBIN', 'instrument_key': 'DHAN_3045'},
    ]
    
    # Test date: yesterday
    test_date = datetime.now() - timedelta(days=1)
    test_date = test_date.replace(hour=10, minute=0, second=0, microsecond=0)
    
    logger.info("="*80)
    logger.info("SCANNER DIAGNOSTICS")
    logger.info("="*80)
    logger.info(f"Test Date: {test_date.strftime('%Y-%m-%d %H:%M')}")
    logger.info("")
    
    for stock in test_stocks:
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing: {stock['symbol']} ({stock['instrument_key']})")
        logger.info(f"{'='*80}")
        
        # Get daily volume stats
        stats = daily_service.get_volume_statistics(stock['instrument_key'], days=20)
        logger.info(f"\nDaily Volume Statistics:")
        logger.info(f"  Avg Daily Volume: {stats['avg_volume']:,.0f}")
        logger.info(f"  Avg Volume/Minute: {stats['avg_volume_per_minute']:,.0f}")
        logger.info(f"  Days Analyzed: {stats['days_analyzed']}")
        
        # Get intraday data
        start_time = test_date.replace(hour=9, minute=15)
        end_time = test_date.replace(hour=15, minute=30)
        
        candles = db.query(Candle).filter(
            and_(
                Candle.instrument_key == stock['instrument_key'],
                Candle.interval == '1minute',
                Candle.timestamp >= start_time,
                Candle.timestamp <= end_time
            )
        ).order_by(Candle.timestamp.desc()).limit(100).all()
        
        if not candles:
            logger.warning(f"  ⚠️  No intraday data found")
            continue
        
        logger.info(f"\nIntraday Data:")
        logger.info(f"  Candles Available: {len(candles)}")
        
        # Convert to DataFrame
        data = []
        for candle in candles:
            data.append({
                'timestamp': candle.timestamp,
                'open': candle.open,
                'high': candle.high,
                'low': candle.low,
                'close': candle.close,
                'volume': candle.volume
            })
        
        df = pd.DataFrame(data)
        
        # Analyze volume ratios
        logger.info(f"\nVolume Analysis:")
        logger.info(f"  Recent Volume (latest candle): {df['volume'].iloc[0]:,.0f}")
        
        # Calculate volume ratio using daily baseline
        spec3 = importlib.util.spec_from_file_location("technical_indicators", "pkscreener-integration/technical_indicators.py")
        ti_module = importlib.util.module_from_spec(spec3)
        spec3.loader.exec_module(ti_module)
        ti = ti_module.TechnicalIndicators()
        
        volume_ratio = ti.calculate_intraday_volume_ratio(
            df['volume'].iloc[0],
            stock['instrument_key'],
            daily_service
        )
        logger.info(f"  Volume Ratio (vs daily avg/min): {volume_ratio:.2f}x")
        logger.info(f"  Passes 2.0x threshold: {volume_ratio >= 2.0}")
        
        # Check momentum
        if len(df) >= 2:
            green_candles = 0
            for i in range(min(2, len(df))):
                if df['close'].iloc[i] > df['open'].iloc[i]:
                    green_candles += 1
            
            closes = list(df['close'].head(2))
            closes_ascending = closes == sorted(closes, reverse=True)
            
            logger.info(f"\nMomentum Analysis:")
            logger.info(f"  Green Candles (last 2): {green_candles}/2")
            logger.info(f"  Closes Ascending: {closes_ascending}")
            logger.info(f"  Passes Momentum: {green_candles == 2 and closes_ascending}")
        
        # Check breakout
        if len(df) >= 11:
            current_close = df['close'].iloc[0]
            lookback_high = df['high'].iloc[1:11].max()
            breakout = current_close > lookback_high
            
            logger.info(f"\nBreakout Analysis:")
            logger.info(f"  Current Close: {current_close:.2f}")
            logger.info(f"  10-min High: {lookback_high:.2f}")
            logger.info(f"  Passes Breakout: {breakout}")
        
        # Run scanner
        logger.info(f"\nScanner #1 Result:")
        passed, metrics = strategies.scanner_1_volume_momentum_breakout_atr(df, stock['instrument_key'])
        logger.info(f"  Passed: {passed}")
        logger.info(f"  Metrics: {metrics}")
    
    db.close()
    logger.info("\n" + "="*80)
    logger.info("DIAGNOSIS COMPLETE")
    logger.info("="*80)


if __name__ == "__main__":
    diagnose()

