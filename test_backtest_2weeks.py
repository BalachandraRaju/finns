"""
Test PKScreener Backtest for Past 2 Weeks
Tests the new daily volume baseline integration
"""
import sys
import os
from datetime import datetime, timedelta

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pkscreener-integration'))

from app.db import get_db

# Import from pkscreener-integration directory
import importlib.util
spec = importlib.util.spec_from_file_location("backtest_engine", "pkscreener-integration/backtest_engine.py")
backtest_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backtest_module)
BacktestEngine = backtest_module.BacktestEngine

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_backtest_2weeks():
    """Run backtest for past 2 weeks"""
    
    # Calculate date range (past 2 weeks)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=14)
    
    logger.info("="*80)
    logger.info("PKScreener Backtest - Past 2 Weeks")
    logger.info("="*80)
    logger.info(f"Start Date: {start_date.strftime('%Y-%m-%d')}")
    logger.info(f"End Date: {end_date.strftime('%Y-%m-%d')}")
    logger.info("")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Initialize backtest engine
        logger.info("Initializing backtest engine with daily volume baseline...")
        engine = BacktestEngine(db)
        
        # Run backtest for scanners 1 and 12 (volume-based scanners)
        scanner_ids = [1, 12]
        
        logger.info(f"Running backtest for scanners: {scanner_ids}")
        logger.info(f"Stocks in watchlist: {len(engine.watchlist)}")
        logger.info("")
        
        # Run backtest
        results = engine.run_backtest(
            scanner_ids=scanner_ids,
            start_date=start_date,
            end_date=end_date,
            max_stocks=None  # All stocks
        )
        
        # Display results
        logger.info("="*80)
        logger.info("BACKTEST RESULTS")
        logger.info("="*80)
        
        for scanner_id in scanner_ids:
            scanner_results = [r for r in results if r.scanner_id == scanner_id]
            
            logger.info(f"\nScanner #{scanner_id}:")
            logger.info(f"  Total Alerts: {len(scanner_results)}")
            
            if scanner_results:
                # Calculate success metrics
                successful = [r for r in scanner_results if r.was_successful]
                success_rate = (len(successful) / len(scanner_results)) * 100
                
                # Calculate average returns
                avg_return_3min = sum([r.return_3min_pct or 0 for r in scanner_results]) / len(scanner_results)
                avg_return_5min = sum([r.return_5min_pct or 0 for r in scanner_results]) / len(scanner_results)
                avg_return_15min = sum([r.return_15min_pct or 0 for r in scanner_results]) / len(scanner_results)
                
                logger.info(f"  Successful Alerts: {len(successful)} ({success_rate:.1f}%)")
                logger.info(f"  Avg Return (3min): {avg_return_3min:.2f}%")
                logger.info(f"  Avg Return (5min): {avg_return_5min:.2f}%")
                logger.info(f"  Avg Return (15min): {avg_return_15min:.2f}%")
                
                # Show top 5 alerts
                logger.info(f"\n  Top 5 Alerts by 3-min Return:")
                sorted_results = sorted(scanner_results, key=lambda x: x.return_3min_pct or 0, reverse=True)
                for i, r in enumerate(sorted_results[:5], 1):
                    logger.info(f"    {i}. {r.symbol} @ {r.trigger_time.strftime('%Y-%m-%d %H:%M')} - "
                              f"Return: {r.return_3min_pct:.2f}% (Volume Ratio: {r.metrics.get('volume_ratio', 0):.2f}x)")
        
        logger.info("")
        logger.info("="*80)
        logger.info(f"TOTAL ALERTS GENERATED: {len(results)}")
        logger.info("="*80)
        
        # Save results to database
        logger.info("\nSaving results to database...")
        for result in results:
            db.add(result)
        db.commit()
        logger.info(f"✅ Saved {len(results)} results to database")
        
    except Exception as e:
        logger.error(f"Error running backtest: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    run_backtest_2weeks()

