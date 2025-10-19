"""
PKScreener Scheduler
Runs scanners every 3 minutes during market hours
COMPLETELY SEPARATE from existing P&F scheduler in app/scheduler.py
"""
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz
import logging

from app.db import get_db
from scanner_engine import ScannerEngine

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None
scanner_engine = None


def is_market_hours() -> bool:
    """
    Check if current time is within market hours
    Market hours: 9:15 AM - 3:30 PM IST, Monday-Friday
    """
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    # Check if weekend
    if now.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    
    # Check time
    market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    return market_start <= now <= market_end


def run_scanners_job():
    """
    Job function to run scanners
    Called every 3 minutes by scheduler
    """
    global scanner_engine
    
    # Double-check market hours
    if not is_market_hours():
        logger.info("⏸️  Outside market hours - skipping scanner run")
        return
    
    try:
        logger.info("🔍 Running PKScreener scanners...")
        
        # Get database session
        db = next(get_db())
        
        # Create scanner engine if not exists
        if scanner_engine is None:
            scanner_engine = ScannerEngine(db)
        
        # Run all 5 scanners
        results = scanner_engine.scan_all_stocks(scanner_ids=[1, 12, 14, 20, 21])
        
        # Log summary
        total_triggers = sum(len(r) for r in results.values())
        logger.info(f"✅ Scanner run complete: {total_triggers} total triggers")
        
        for scanner_id, scanner_results in results.items():
            if scanner_results:
                logger.info(f"  Scanner #{scanner_id}: {len(scanner_results)} triggers")
                for result in scanner_results[:3]:  # Log top 3
                    logger.info(f"    • {result.symbol}: ₹{result.trigger_price:.2f}")
        
        db.close()
        
    except Exception as e:
        logger.error(f"❌ Error running scanners: {e}", exc_info=True)


def start_scheduler():
    """
    Start the PKScreener scheduler
    Runs scanners every 3 minutes during market hours
    """
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already running")
        return
    
    logger.info("Starting PKScreener scheduler...")
    
    # Create scheduler with IST timezone
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Kolkata'))
    
    # Add job to run every 3 minutes during market hours
    # Runs Mon-Fri, 9:15 AM - 3:30 PM
    scheduler.add_job(
        run_scanners_job,
        'cron',
        day_of_week='mon-fri',
        hour='9-15',
        minute='*/3',  # Every 3 minutes
        id='pkscreener_job',
        name='PKScreener Scanner Job',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ PKScreener scheduler started - runs every 3 minutes during market hours")
    logger.info("   Market hours: Mon-Fri, 9:15 AM - 3:30 PM IST")


def stop_scheduler():
    """Stop the PKScreener scheduler"""
    global scheduler
    
    if scheduler is None:
        logger.warning("Scheduler not running")
        return
    
    scheduler.shutdown()
    scheduler = None
    logger.info("PKScreener scheduler stopped")


def get_scheduler_status() -> dict:
    """Get scheduler status information"""
    global scheduler
    
    if scheduler is None:
        return {
            'running': False,
            'next_run': None,
            'market_hours': is_market_hours()
        }
    
    jobs = scheduler.get_jobs()
    next_run = None
    
    if jobs:
        next_run = jobs[0].next_run_time
    
    return {
        'running': True,
        'next_run': next_run,
        'market_hours': is_market_hours(),
        'jobs': len(jobs)
    }


def main():
    """Test the scheduler"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*80)
    print("PKSCREENER SCHEDULER TEST")
    print("="*80)
    
    # Check market hours
    market_hours = is_market_hours()
    print(f"\nCurrent time: {datetime.now(pytz.timezone('Asia/Kolkata'))}")
    print(f"Market hours: {'YES ✅' if market_hours else 'NO ⏸️'}")
    
    # Start scheduler
    print("\nStarting scheduler...")
    start_scheduler()
    
    # Get status
    status = get_scheduler_status()
    print(f"\nScheduler Status:")
    print(f"  Running: {status['running']}")
    print(f"  Next run: {status['next_run']}")
    print(f"  Market hours: {status['market_hours']}")
    
    # Run once manually for testing
    if market_hours:
        print("\n" + "="*80)
        print("Running scanners manually for testing...")
        print("="*80)
        run_scanners_job()
    else:
        print("\n⏸️  Outside market hours - scheduler will run during market hours")
    
    print("\n✅ Scheduler test complete!")
    print("Scheduler is running in background. Press Ctrl+C to stop.")
    
    try:
        # Keep running
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n\nStopping scheduler...")
        stop_scheduler()
        print("✅ Scheduler stopped")


if __name__ == "__main__":
    main()

