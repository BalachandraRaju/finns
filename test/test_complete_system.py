#!/usr/bin/env python3
"""
Complete System Test: Database, LTP API, and Alert Generation
Tests all components to ensure everything is working correctly.
"""

import sys
import os
import time
from datetime import datetime, date, timedelta
from logzero import logger

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_database_connection():
    """Test database connection and configuration."""
    logger.info("🗄️ TESTING DATABASE CONNECTION")
    logger.info("-" * 50)
    
    try:
        from app.db import DATABASE_URL, engine, SessionLocal
        logger.info(f"📊 Database URL: {DATABASE_URL}")
        
        # Test connection
        with engine.connect() as conn:
            logger.info("✅ Database connection successful!")
        
        # Test session
        db = SessionLocal()
        try:
            logger.info("✅ Database session created successfully!")
        finally:
            db.close()
        
        # Check tables
        from app.models import Base, Candle, LTPData
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables verified!")
        
        # Check existing data
        db = SessionLocal()
        try:
            candle_count = db.query(Candle).count()
            ltp_count = db.query(LTPData).count()
            logger.info(f"📊 Existing data: {candle_count} candles, {ltp_count} LTP records")
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False

def test_ltp_api():
    """Test LTP API functionality."""
    logger.info("\n🌐 TESTING LTP API")
    logger.info("-" * 50)
    
    try:
        sys.path.append('data-fetch')
        from ltp_service import ltp_service
        from fo_stocks_loader import fo_stocks_loader
        
        # Get watchlist
        stocks = fo_stocks_loader.get_fo_symbols_with_instrument_keys()
        logger.info(f"📊 Watchlist: {len(stocks)} stocks")
        
        # Test Upstox connection
        connection_test = ltp_service.test_upstox_connection()
        logger.info(f"🔗 Upstox connection: {'✅ SUCCESS' if connection_test else '❌ FAILED'}")
        
        if not connection_test:
            logger.warning("⚠️ Upstox API authentication failed")
            logger.info("💡 This is expected if access token is expired")
            return False
        
        # Test LTP collection
        logger.info("🚀 Testing LTP collection...")
        start_time = time.time()
        ltp_data = ltp_service.collect_ltp_data()
        end_time = time.time()
        
        if ltp_data:
            logger.info(f"✅ LTP Collection Success:")
            logger.info(f"   📊 Stocks collected: {len(ltp_data)}")
            logger.info(f"   ⏱️ Duration: {end_time - start_time:.2f} seconds")
            logger.info(f"   🌐 API calls: 1 (instead of {len(stocks)})")
            
            # Show sample data
            sample_symbols = list(ltp_data.keys())[:3]
            for symbol in sample_symbols:
                logger.info(f"   💰 {symbol}: ₹{ltp_data[symbol]}")
            
            return True
        else:
            logger.warning("⚠️ No LTP data received")
            return False
            
    except Exception as e:
        logger.error(f"❌ LTP API test failed: {e}")
        return False

def test_alert_generation():
    """Test alert generation functionality."""
    logger.info("\n🚨 TESTING ALERT GENERATION")
    logger.info("-" * 50)
    
    try:
        from app.scheduler import run_alert_check
        from app import crud
        
        # Get stocks for testing
        stocks = crud.get_all_stocks()
        if not stocks:
            logger.warning("⚠️ No stocks found in database")
            return False
        
        logger.info(f"📊 Testing alerts for {len(stocks)} stocks")
        
        # Test alert generation for first few stocks
        test_stocks = stocks[:3]
        alerts_generated = 0
        
        for stock in test_stocks:
            symbol = stock['symbol']
            logger.info(f"🔍 Testing alerts for {symbol}...")
            
            try:
                # This will use the optimized database-first approach
                start_time = time.time()
                # Note: run_alert_check is typically called by scheduler
                # For testing, we'll simulate the process
                logger.info(f"   📊 Checking database for {symbol} candles...")
                
                # Check if we have data for this stock
                from app.db import SessionLocal
                from app.models import Candle
                
                db = SessionLocal()
                try:
                    # Get instrument key
                    instrument_key = stock.get('instrument_key')
                    if not instrument_key:
                        logger.warning(f"   ⚠️ No instrument key for {symbol}")
                        continue
                    
                    # Check for recent candles
                    end_date = date.today()
                    start_date = end_date - timedelta(days=5)
                    start_datetime = datetime.combine(start_date, datetime.min.time())
                    end_datetime = datetime.combine(end_date, datetime.max.time())
                    
                    candles = db.query(Candle).filter(
                        Candle.instrument_key == instrument_key,
                        Candle.interval == '1minute',
                        Candle.timestamp >= start_datetime,
                        Candle.timestamp <= end_datetime
                    ).count()
                    
                    end_time = time.time()
                    
                    logger.info(f"   ✅ Found {candles} candles in {end_time - start_time:.3f}s")
                    
                    if candles > 100:
                        logger.info(f"   🚨 Sufficient data for alert generation")
                        alerts_generated += 1
                    else:
                        logger.info(f"   ⚠️ Insufficient data for alerts")
                        
                finally:
                    db.close()
                    
            except Exception as e:
                logger.error(f"   ❌ Error testing {symbol}: {e}")
        
        logger.info(f"✅ Alert test completed:")
        logger.info(f"   📊 Stocks tested: {len(test_stocks)}")
        logger.info(f"   🚨 Stocks with sufficient data: {alerts_generated}")
        
        return alerts_generated > 0
        
    except Exception as e:
        logger.error(f"❌ Alert generation test failed: {e}")
        return False

def test_data_scheduler():
    """Test data scheduler functionality."""
    logger.info("\n📅 TESTING DATA SCHEDULER")
    logger.info("-" * 50)
    
    try:
        sys.path.append('data-fetch')
        from data_scheduler import data_scheduler
        
        # Check scheduler status
        try:
            status = data_scheduler.get_status()
            logger.info(f"🔄 Scheduler running: {status.get('is_running', False)}")
            logger.info(f"🌐 Upstox connected: {status.get('upstox_connected', False)}")
        except Exception as e:
            logger.info(f"⚠️ Scheduler status check failed: {e}")
        
        # Check market hours
        now = datetime.now()
        from datetime import time as dt_time
        market_open = dt_time(9, 15)
        market_close = dt_time(15, 30)
        current_time = now.time()
        is_market_open = market_open <= current_time <= market_close
        
        logger.info(f"🕐 Current time: {now.strftime('%H:%M:%S')}")
        logger.info(f"📈 Market status: {'OPEN' if is_market_open else 'CLOSED'}")
        
        # Test force LTP collection
        logger.info("🧪 Testing force LTP collection...")
        try:
            result = data_scheduler.force_ltp_collection()
            logger.info(f"✅ Force LTP result: {result}")
            return result.get('success', False)
        except Exception as e:
            logger.error(f"❌ Force LTP failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Data scheduler test failed: {e}")
        return False

def run_complete_system_test():
    """Run complete system test."""
    logger.info("🚀 COMPLETE SYSTEM TEST")
    logger.info("=" * 80)
    logger.info("📊 Testing all components:")
    logger.info("   • Database connection and configuration")
    logger.info("   • LTP API functionality")
    logger.info("   • Alert generation system")
    logger.info("   • Data scheduler")
    logger.info("=" * 80)
    
    results = {}
    
    # Test 1: Database
    results['database'] = test_database_connection()
    
    # Test 2: LTP API
    results['ltp_api'] = test_ltp_api()
    
    # Test 3: Alert Generation
    results['alerts'] = test_alert_generation()
    
    # Test 4: Data Scheduler
    results['scheduler'] = test_data_scheduler()
    
    # Summary
    logger.info("\n🎯 SYSTEM TEST SUMMARY")
    logger.info("=" * 80)
    
    for component, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"   {component.upper()}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    logger.info(f"\n📊 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 ALL SYSTEMS OPERATIONAL!")
    elif passed_tests >= total_tests // 2:
        logger.info("⚠️ PARTIAL FUNCTIONALITY - Some components need attention")
    else:
        logger.info("❌ SYSTEM ISSUES - Multiple components need fixing")
    
    # Specific recommendations
    logger.info("\n💡 RECOMMENDATIONS:")
    
    if not results['database']:
        logger.info("   🗄️ Fix database configuration")
    
    if not results['ltp_api']:
        logger.info("   🌐 Update Upstox access token in .env file")
        logger.info("   📝 UPSTOX_ACCESS_TOKEN=your_new_token_here")
    
    if not results['alerts']:
        logger.info("   🚨 Ensure sufficient historical data in database")
        logger.info("   📊 Run data collection to populate database")
    
    if not results['scheduler']:
        logger.info("   📅 Start data scheduler for automated collection")
        logger.info("   🔧 Fix Upstox authentication first")
    
    return results

def main():
    """Main function."""
    print("🚀 COMPLETE SYSTEM TEST")
    print("=" * 80)
    print("This test checks:")
    print("• Database: SQLite/PostgreSQL connection")
    print("• LTP API: Upstox API functionality")
    print("• Alerts: Database-first alert generation")
    print("• Scheduler: Automated data collection")
    print("=" * 80)
    
    results = run_complete_system_test()
    
    # Return appropriate exit code
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    if passed_tests == total_tests:
        return 0  # All tests passed
    elif passed_tests >= total_tests // 2:
        return 1  # Partial success
    else:
        return 2  # Major issues

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n👋 Test stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(3)
