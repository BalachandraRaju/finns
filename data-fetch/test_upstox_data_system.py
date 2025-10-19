#!/usr/bin/env python3
"""
Comprehensive test script for Upstox-based data collection system.
Tests LTP collection, historical data backfill, and scheduler functionality.
"""

import sys
import os
import time

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from datetime import datetime
from logzero import logger

# Import our services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from upstox_ltp_client import upstox_ltp_client
from ltp_service import ltp_service
from backfill_service import backfill_service
from data_scheduler import data_scheduler

def test_database_setup():
    """Test database setup (PostgreSQL preferred, SQLite fallback)."""
    print("\n" + "="*60)
    print("🗄️ TESTING DATABASE SETUP")
    print("="*60)

    try:
        from data_fetch.postgres_config import postgres_config

        # Test PostgreSQL availability
        postgres_available = postgres_config.is_postgres_available()

        if postgres_available:
            print("✅ PostgreSQL connection successful!")
            print("🐘 Using PostgreSQL database")

            # Setup PostgreSQL for data collection
            setup_success = postgres_config.setup_postgres_for_data_collection()
            if setup_success:
                print("✅ PostgreSQL setup completed")
                return True
            else:
                print("❌ PostgreSQL setup failed")
                return False
        else:
            print("⚠️ PostgreSQL not available, using SQLite fallback")
            print("📁 Using SQLite database")
            return True

    except Exception as e:
        print(f"❌ Database setup error: {e}")
        return False

def test_fo_stocks_loading():
    """Test F&O stocks loading from file."""
    print("\n" + "="*60)
    print("📋 TESTING F&O STOCKS LOADING")
    print("="*60)

    try:
        from data_fetch.fo_stocks_loader import fo_stocks_loader

        # Test loading F&O stocks from file
        fo_symbols = fo_stocks_loader.load_fo_stocks_from_file()

        if fo_symbols:
            print(f"✅ Loaded {len(fo_symbols)} F&O symbols from file")
            print(f"📊 Sample symbols: {fo_symbols[:5]}")

            # Test getting symbols for data collection
            collection_symbols = fo_stocks_loader.get_stock_symbols_for_data_collection()
            print(f"📈 {len(collection_symbols)} symbols ready for data collection")

            # Test validation
            validation_success = fo_stocks_loader.validate_fo_stocks_setup()
            if validation_success:
                print("✅ F&O stocks validation passed")
                return True
            else:
                print("❌ F&O stocks validation failed")
                return False
        else:
            print("❌ No F&O symbols loaded")
            return False

    except Exception as e:
        print(f"❌ F&O stocks loading error: {e}")
        return False

def test_upstox_connection():
    """Test basic Upstox API connection."""
    print("\n" + "="*60)
    print("🔌 TESTING UPSTOX API CONNECTION")
    print("="*60)

    try:
        success = upstox_ltp_client.test_connection()

        if success:
            print("✅ Upstox connection test passed!")
            return True
        else:
            print("❌ Upstox connection test failed!")
            return False

    except Exception as e:
        print(f"❌ Connection test error: {e}")
        return False

def test_ltp_collection():
    """Test LTP data collection using Upstox LTP API v3."""
    print("\n" + "="*60)
    print("📊 TESTING LTP DATA COLLECTION")
    print("="*60)
    
    try:
        # Test basic LTP collection
        print("📊 Testing LTP collection for watchlist...")
        ltp_data = upstox_ltp_client.get_watchlist_ltp()
        
        if ltp_data:
            print(f"✅ LTP collection successful!")
            print(f"📈 Collected data for {len(ltp_data)} symbols")
            
            # Show sample data
            sample_symbols = list(ltp_data.keys())[:3]
            for symbol in sample_symbols:
                data = ltp_data[symbol]
                ltp = data.get('last_price', 'N/A')
                volume = data.get('volume', 'N/A')
                change_pct = data.get('change_percent', 'N/A')
                print(f"   {symbol}: ₹{ltp} (Vol: {volume}, Change: {change_pct}%)")
            
            return True
        else:
            print("❌ No LTP data received")
            return False
            
    except Exception as e:
        print(f"❌ LTP collection test error: {e}")
        return False

def test_ltp_service():
    """Test LTP service functionality."""
    print("\n" + "="*60)
    print("🔧 TESTING LTP SERVICE")
    print("="*60)
    
    try:
        # Test connection
        print("🔗 Testing Upstox connection...")
        if not ltp_service.test_upstox_connection():
            print("❌ Upstox connection failed")
            return False
        
        print("✅ Upstox connection successful")
        
        # Test LTP collection
        print("📊 Testing LTP service collection...")
        ltp_data = ltp_service.collect_ltp_data()
        
        if ltp_data:
            print(f"✅ LTP service successful! Collected data for {len(ltp_data)} symbols")
            
            # Test data retrieval
            symbols = list(ltp_data.keys())
            if symbols:
                test_symbol = symbols[0]
                latest_ltp = ltp_service.get_latest_ltp(test_symbol)
                
                if latest_ltp:
                    print(f"✅ Latest LTP for {test_symbol}: ₹{latest_ltp}")
                else:
                    print(f"⚠️ Could not retrieve latest LTP for {test_symbol}")
            
            return True
        else:
            print("❌ LTP service failed")
            return False
            
    except Exception as e:
        print(f"❌ LTP service test error: {e}")
        return False

def test_backfill_service():
    """Test backfill service functionality."""
    print("\n" + "="*60)
    print("🔄 TESTING BACKFILL SERVICE")
    print("="*60)
    
    try:
        # Get first symbol from watchlist
        ltp_data = upstox_ltp_client.get_watchlist_ltp()
        if not ltp_data:
            print("⚠️ No symbols found for backfill test")
            return False
        
        test_symbol = list(ltp_data.keys())[0]
        print(f"🔍 Testing backfill for: {test_symbol}")
        
        # Check missing data
        missing_ranges = backfill_service.detect_missing_data(test_symbol, days_back=7)
        print(f"📊 Found {len(missing_ranges)} missing data ranges")
        
        if missing_ranges:
            print("📅 Missing ranges:")
            for start, end in missing_ranges:
                print(f"   {start} to {end}")
        
        # Test backfill logic (dry run)
        print("🔄 Testing backfill logic...")
        needs_backfill = backfill_service._needs_backfill(test_symbol)
        print(f"   Needs backfill: {needs_backfill}")
        
        # Get sync status
        sync_report = backfill_service.get_sync_status_report()
        if test_symbol in sync_report:
            print(f"📋 Sync status for {test_symbol}:")
            for data_type, status in sync_report[test_symbol].items():
                print(f"   {data_type}: {status['status']}")
        
        print("✅ Backfill service test completed")
        return True
        
    except Exception as e:
        print(f"❌ Backfill service test error: {e}")
        return False

def test_data_freshness():
    """Test data freshness checking."""
    print("\n" + "="*60)
    print("🕐 TESTING DATA FRESHNESS")
    print("="*60)
    
    try:
        freshness_report = ltp_service.check_data_freshness()
        
        if freshness_report:
            print(f"📊 Freshness report for {len(freshness_report)} symbols:")
            
            for symbol, data in list(freshness_report.items())[:5]:  # Show first 5
                status = data.get('status', 'unknown')
                minutes_ago = data.get('minutes_ago', 'N/A')
                is_stale = data.get('is_stale', True)
                
                stale_indicator = "🔴" if is_stale else "🟢"
                print(f"   {stale_indicator} {symbol}: {status}, {minutes_ago} min ago")
            
            if len(freshness_report) > 5:
                print(f"   ... and {len(freshness_report) - 5} more symbols")
            
            print("✅ Data freshness check completed")
            return True
        else:
            print("⚠️ No freshness data available")
            return False
            
    except Exception as e:
        print(f"❌ Data freshness test error: {e}")
        return False

def test_scheduler_status():
    """Test scheduler status and configuration."""
    print("\n" + "="*60)
    print("⏰ TESTING SCHEDULER STATUS")
    print("="*60)
    
    try:
        status = data_scheduler.get_status()
        
        print(f"🔧 Scheduler running: {status['is_running']}")
        print(f"📈 Market open: {status['market_open']}")
        print(f"🔌 Upstox connected: {status['upstox_connected']}")
        
        if status['next_jobs']:
            print("📅 Scheduled jobs:")
            for job in status['next_jobs'][:3]:  # Show first 3
                print(f"   {job['job']}: {job['next_run']}")
        
        print("✅ Scheduler status check completed")
        return True
        
    except Exception as e:
        print(f"❌ Scheduler status test error: {e}")
        return False

def test_manual_ltp_trigger():
    """Test manual LTP collection trigger."""
    print("\n" + "="*60)
    print("🔧 TESTING MANUAL LTP TRIGGER")
    print("="*60)
    
    try:
        result = data_scheduler.force_ltp_collection()
        
        if result['success']:
            print(f"✅ Manual LTP collection successful!")
            print(f"📊 Collected data for {result['symbols_collected']} symbols")
            return True
        else:
            print(f"❌ Manual LTP collection failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Manual LTP trigger test error: {e}")
        return False

def run_all_tests():
    """Run all Upstox data system tests."""
    print("🧪 STARTING UPSTOX DATA SYSTEM TESTS")
    print("="*60)
    
    tests = [
        ("Database Setup", test_database_setup),
        ("F&O Stocks Loading", test_fo_stocks_loading),
        ("Upstox Connection", test_upstox_connection),
        ("LTP Collection", test_ltp_collection),
        ("LTP Service", test_ltp_service),
        ("Backfill Service", test_backfill_service),
        ("Data Freshness", test_data_freshness),
        ("Scheduler Status", test_scheduler_status),
        ("Manual LTP Trigger", test_manual_ltp_trigger),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results[test_name] = False
        
        # Small delay between tests
        time.sleep(1)
    
    # Summary
    print("\n" + "="*60)
    print("📋 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Upstox data system is ready.")
        print("\n💡 Next steps:")
        print("1. Start the data scheduler: data_scheduler.start()")
        print("2. Monitor LTP collection during market hours")
        print("3. Check backfill operations for historical data")
    else:
        print("⚠️ Some tests failed. Please check the configuration.")
        print("\n🔧 Common issues:")
        print("1. Check UPSTOX_ACCESS_TOKEN in environment")
        print("2. Verify Upstox API access is enabled")
        print("3. Ensure database tables are created")
    
    return passed == total

if __name__ == "__main__":
    print("🚀 Upstox Data Collection System Test Suite")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("app"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Run tests
    success = run_all_tests()
    
    if success:
        print("\n🎉 All systems go! You can now start the data collection system.")
        print("💡 To start: python -c 'from data_fetch.data_scheduler import data_scheduler; data_scheduler.start()'")
    else:
        print("\n🔧 Please fix the failing tests before proceeding.")
    
    sys.exit(0 if success else 1)
