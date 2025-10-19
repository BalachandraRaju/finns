"""
Comprehensive Backtest for PKScreener-style Breakout Scanners
Tests scanners 1, 17, 20, 23, 32 on past 2 weeks of data
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
import logging

# Import modules
spec = importlib.util.spec_from_file_location("daily_data_service", "pkscreener-integration/daily_data_service.py")
daily_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(daily_module)

spec2 = importlib.util.spec_from_file_location("breakout_scanners", "pkscreener-integration/breakout_scanners.py")
breakout_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(breakout_module)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_daily_candles_from_mongo(instrument_key: str, days: int = 250):
    """Fetch daily candles from MongoDB for 52-week calculations"""
    try:
        from pymongo import MongoClient
        import os
        
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        client = MongoClient(mongo_uri)
        db = client['trading_data']
        
        # Get daily candles
        candles = list(db.daily_candles.find(
            {'instrument_key': instrument_key},
            {'_id': 0, 'date': 1, 'open': 1, 'high': 1, 'low': 1, 'close': 1, 'volume': 1}
        ).sort('date', -1).limit(days))
        
        if not candles:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(candles)
        df = df.sort_values('date', ascending=False).reset_index(drop=True)
        
        client.close()
        return df
        
    except Exception as e:
        logger.error(f"Error fetching daily candles: {e}")
        return None


def run_backtest():
    """Run comprehensive backtest on all breakout scanners"""
    
    db = next(get_db())
    daily_service = daily_module.get_daily_data_service()
    scanners = breakout_module.get_breakout_scanners(daily_data_service=daily_service)
    
    # Get watchlist
    stocks = get_watchlist_details()
    logger.info(f"Testing {len(stocks)} stocks")
    
    # Test period: past 2 weeks
    end_date = datetime.now()
    start_date = end_date - timedelta(days=14)
    
    logger.info("="*100)
    logger.info("PKScreener BREAKOUT SCANNERS BACKTEST")
    logger.info("="*100)
    logger.info(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    logger.info(f"Stocks: {len(stocks)}")
    logger.info("")
    
    # Results storage
    results = {
        1: [],   # Probable Breakout
        17: [],  # 52-Week High Breakout
        20: [],  # Bullish for Tomorrow
        23: [],  # Breaking Out Now
        32: [],  # Intraday Breakout Setup
    }
    
    # Test each stock
    for idx, stock in enumerate(stocks, 1):
        if idx % 50 == 0:
            logger.info(f"Progress: {idx}/{len(stocks)} stocks processed...")
        
        # Get intraday data for yesterday (most recent complete day)
        test_date = datetime.now() - timedelta(days=1)
        test_date = test_date.replace(hour=10, minute=30, second=0, microsecond=0)
        
        start_time = test_date - timedelta(hours=2)
        end_time = test_date + timedelta(minutes=30)
        
        candles = db.query(Candle).filter(
            and_(
                Candle.instrument_key == stock.instrument_key,
                Candle.interval == '1minute',
                Candle.timestamp >= start_time,
                Candle.timestamp <= end_time
            )
        ).order_by(Candle.timestamp.desc()).limit(100).all()
        
        if not candles or len(candles) < 30:
            continue
        
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
        
        # Get daily candles for 52-week scanner
        daily_df = get_daily_candles_from_mongo(stock.instrument_key, days=250)
        
        # Test Scanner #1: Probable Breakout
        try:
            passed, metrics = scanners.scanner_1_probable_breakout(df, stock.instrument_key)
            if passed:
                results[1].append({
                    'symbol': stock.symbol,
                    'timestamp': test_date,
                    'metrics': metrics
                })
        except Exception as e:
            pass
        
        # Test Scanner #17: 52-Week High Breakout
        try:
            passed, metrics = scanners.scanner_17_52week_high_breakout(df, daily_df)
            if passed:
                results[17].append({
                    'symbol': stock.symbol,
                    'timestamp': test_date,
                    'metrics': metrics
                })
        except Exception as e:
            pass
        
        # Test Scanner #20: Bullish for Tomorrow
        try:
            passed, metrics = scanners.scanner_20_bullish_for_tomorrow(df)
            if passed:
                results[20].append({
                    'symbol': stock.symbol,
                    'timestamp': test_date,
                    'metrics': metrics
                })
        except Exception as e:
            pass
        
        # Test Scanner #23: Breaking Out Now
        try:
            passed, metrics = scanners.scanner_23_breaking_out_now(df, stock.instrument_key)
            if passed:
                results[23].append({
                    'symbol': stock.symbol,
                    'timestamp': test_date,
                    'metrics': metrics
                })
        except Exception as e:
            pass
        
        # Test Scanner #32: Intraday Breakout Setup
        try:
            passed, metrics = scanners.scanner_32_intraday_breakout_setup(df, stock.instrument_key)
            if passed:
                results[32].append({
                    'symbol': stock.symbol,
                    'timestamp': test_date,
                    'metrics': metrics
                })
        except Exception as e:
            pass
    
    # Display results
    logger.info("")
    logger.info("="*100)
    logger.info("BACKTEST RESULTS")
    logger.info("="*100)
    
    total_alerts = 0
    
    for scanner_id in [1, 17, 20, 23, 32]:
        scanner_results = results[scanner_id]
        total_alerts += len(scanner_results)
        
        logger.info(f"\nScanner #{scanner_id}: {len(scanner_results)} alerts")
        
        if scanner_results:
            logger.info(f"  Top 10 stocks:")
            for i, result in enumerate(scanner_results[:10], 1):
                metrics_str = ", ".join([f"{k}: {v}" for k, v in result['metrics'].items() if k not in ['scanner_id', 'scanner_name', 'error']])
                logger.info(f"    {i}. {result['symbol']} - {metrics_str[:100]}")
    
    logger.info("")
    logger.info("="*100)
    logger.info(f"TOTAL ALERTS GENERATED: {total_alerts}")
    logger.info(f"Average alerts per scanner: {total_alerts / 5:.1f}")
    logger.info("="*100)
    
    db.close()
    
    return results


if __name__ == "__main__":
    results = run_backtest()

