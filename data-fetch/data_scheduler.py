"""
Data collection scheduler for automated LTP and historical data collection.
Runs during market hours and handles backfill operations.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import schedule
import time
import threading
from datetime import datetime, time as dt_time
from logzero import logger

# Import services from same directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ltp_service import ltp_service
from backfill_service import backfill_service

class DataScheduler:
    """Scheduler for automated data collection tasks."""
    
    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None
        
        # Market hours (IST)
        self.market_open = dt_time(9, 15)  # 9:15 AM
        self.market_close = dt_time(15, 30)  # 3:30 PM
        
        # Setup schedules
        self._setup_schedules()
    
    def _setup_schedules(self):
        """Setup all scheduled tasks for 1-minute data collection."""

        # LTP collection during market hours (every 1 minute)
        schedule.every(1).minutes.do(self._collect_ltp_if_market_open)

        # Backfill check for missing 1-minute data (every 5 minutes during market hours)
        schedule.every(5).minutes.do(self._backfill_check_if_market_open)

        # Daily backfill for historical 1-minute data (after market close)
        schedule.every().day.at("16:00").do(self._daily_backfill_1min)

        # Weekly full backfill for past 2 months (Sundays)
        schedule.every().sunday.at("10:00").do(self._weekly_full_backfill_2months)

        # Data freshness check (every 2 minutes)
        schedule.every(2).minutes.do(self._check_data_freshness)

        logger.info("📅 1-minute data collection schedules configured")
    
    def _is_market_open(self) -> bool:
        """Check if market is currently open."""
        now = datetime.now().time()
        current_day = datetime.now().weekday()  # Monday=0, Sunday=6
        
        # Market is closed on weekends
        if current_day >= 5:  # Saturday=5, Sunday=6
            return False
        
        # Check if current time is within market hours
        return self.market_open <= now <= self.market_close
    
    def _collect_ltp_if_market_open(self):
        """Collect LTP data only if market is open."""
        if self._is_market_open():
            logger.info("📊 Collecting LTP data (market is open)")
            try:
                ltp_data = ltp_service.collect_ltp_data()
                if ltp_data:
                    logger.info(f"✅ LTP collection successful: {len(ltp_data)} symbols")
                else:
                    logger.warning("⚠️ No LTP data collected")
            except Exception as e:
                logger.error(f"❌ Error during LTP collection: {e}")
        else:
            logger.debug("🔒 Market is closed, skipping LTP collection")
    
    def _backfill_check_if_market_open(self):
        """Check for missing data and backfill if market is open."""
        if self._is_market_open():
            logger.info("🔄 Checking for missing data (market is open)")
            try:
                # Check data freshness
                freshness_report = ltp_service.check_data_freshness()
                stale_symbols = [
                    symbol for symbol, data in freshness_report.items() 
                    if data.get('is_stale', True)
                ]
                
                if stale_symbols:
                    logger.info(f"⚠️ Found {len(stale_symbols)} symbols with stale data")
                    # Trigger immediate LTP collection for stale symbols
                    ltp_service.collect_ltp_data()
                
            except Exception as e:
                logger.error(f"❌ Error during backfill check: {e}")
        else:
            logger.debug("🔒 Market is closed, skipping backfill check")
    
    def _daily_backfill_1min(self):
        """Daily backfill operation for 1-minute data after market close."""
        logger.info("🌅 Starting daily 1-minute data backfill operation")
        try:
            # Backfill 1-minute data for today
            results = backfill_service.backfill_all_symbols_1min(days_back=1, force=False)
            successful = sum(1 for success in results.values() if success)
            logger.info(f"✅ Daily 1-min backfill completed: {successful}/{len(results)} symbols successful")

            # Generate sync status report
            sync_report = backfill_service.get_sync_status_report()
            failed_symbols = [
                symbol for symbol, data in sync_report.items()
                if any(status.get('status') == 'failed' for status in data.values())
            ]

            if failed_symbols:
                logger.warning(f"⚠️ Symbols with sync failures: {failed_symbols}")

        except Exception as e:
            logger.error(f"❌ Error during daily 1-min backfill: {e}")

    def _weekly_full_backfill_2months(self):
        """Weekly full backfill operation for past 2 months of 1-minute data."""
        logger.info("📅 Starting weekly full backfill for past 2 months (1-min data)")
        try:
            # Backfill 1-minute data for past 2 months (60 days)
            results = backfill_service.backfill_all_symbols_1min(days_back=60, force=True)
            successful = sum(1 for success in results.values() if success)
            logger.info(f"✅ Weekly 2-month backfill completed: {successful}/{len(results)} symbols successful")

        except Exception as e:
            logger.error(f"❌ Error during weekly 2-month backfill: {e}")
    
    def _check_data_freshness(self):
        """Check data freshness and log warnings for stale data."""
        try:
            freshness_report = ltp_service.check_data_freshness()
            stale_count = sum(1 for data in freshness_report.values() if data.get('is_stale', True))
            
            if stale_count > 0:
                logger.warning(f"⚠️ {stale_count} symbols have stale data")
                
                # Log details for very stale data (>30 minutes)
                very_stale = [
                    symbol for symbol, data in freshness_report.items()
                    if data.get('minutes_ago', 0) > 30
                ]
                
                if very_stale:
                    logger.warning(f"🚨 Very stale data (>30 min): {very_stale}")
            
        except Exception as e:
            logger.error(f"❌ Error checking data freshness: {e}")
    
    def start(self):
        """Start the data collection scheduler."""
        if self.is_running:
            logger.warning("⚠️ Scheduler is already running")
            return
        
        logger.info("🚀 Starting data collection scheduler...")
        
        # Test Upstox connection first
        if not ltp_service.test_upstox_connection():
            logger.error("❌ Upstox connection test failed. Please check credentials.")
            return
        
        self.is_running = True
        
        # Start scheduler in a separate thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("✅ Data collection scheduler started successfully")
        
        # Run initial data collection if market is open
        if self._is_market_open():
            logger.info("📊 Market is open, running initial data collection...")
            self._collect_ltp_if_market_open()
    
    def stop(self):
        """Stop the data collection scheduler."""
        if not self.is_running:
            logger.warning("⚠️ Scheduler is not running")
            return
        
        logger.info("🛑 Stopping data collection scheduler...")
        self.is_running = False
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        # Clear all scheduled jobs
        schedule.clear()
        
        logger.info("✅ Data collection scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop."""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"❌ Error in scheduler loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def get_status(self) -> dict:
        """Get current scheduler status."""
        return {
            'is_running': self.is_running,
            'market_open': self._is_market_open(),
            'next_jobs': [
                {
                    'job': str(job.job_func),
                    'next_run': job.next_run.isoformat() if job.next_run else None
                }
                for job in schedule.jobs
            ],
            'upstox_connected': ltp_service.test_upstox_connection()
        }
    
    def force_ltp_collection(self) -> dict:
        """Force immediate LTP collection (for testing/manual trigger)."""
        logger.info("🔧 Force triggering LTP collection...")
        try:
            ltp_data = ltp_service.collect_ltp_data()
            return {
                'success': True,
                'symbols_collected': len(ltp_data),
                'data': ltp_data
            }
        except Exception as e:
            logger.error(f"❌ Error during forced LTP collection: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def force_backfill(self, symbol: str = None) -> dict:
        """Force immediate backfill (for testing/manual trigger)."""
        logger.info(f"🔧 Force triggering backfill for {symbol or 'all symbols'}...")
        try:
            if symbol:
                success = backfill_service.backfill_symbol(symbol, force=True)
                return {
                    'success': success,
                    'symbol': symbol
                }
            else:
                results = backfill_service.backfill_all_symbols(force=True)
                successful = sum(1 for success in results.values() if success)
                return {
                    'success': True,
                    'total_symbols': len(results),
                    'successful_symbols': successful,
                    'results': results
                }
        except Exception as e:
            logger.error(f"❌ Error during forced backfill: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Global scheduler instance
data_scheduler = DataScheduler()
