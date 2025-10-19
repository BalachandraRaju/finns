#!/usr/bin/env python3
"""
Test script for AngelOne data fetching functionality.
Validates API connection, LTP collection, and backfill operations.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import time
from datetime import datetime
from logzero import logger

# Import with correct path structure
sys.path.append(os.path.join(project_root, 'data-fetch'))
from angelone_client import angelone_client
from ltp_service import ltp_service
from backfill_service import backfill_service
from data_scheduler import data_scheduler

def test_angelone_connection():
    """Test basic AngelOne API connection."""
    print("\n" + "="*60)
    print("🔌 TESTING ANGELONE API CONNECTION")
    print("="*60)
    
    try:
        # Test authentication
        print("🔐 Testing authentication...")
        success = angelone_client.authenticate()
        
        if success:
            print("✅ Authentication successful!")
            
            # Test connection
            print("🔗 Testing connection...")
            connection_ok = angelone_client.test_connection()
            
            if connection_ok:
                print("✅ Connection test passed!")
                return True
            else:
                print("❌ Connection test failed!")
                return False
        else:
            print("❌ Authentication failed!")
            return False
            
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        return False

def test_ltp_collection():
    """Test LTP data collection."""
    print("\n" + "="*60)
    print("📊 TESTING LTP DATA COLLECTION")
    print("="*60)
    
    try:
        # Get watchlist symbols
        symbols = ltp_service.get_watchlist_symbols()
        print(f"📋 Found {len(symbols)} symbols in watchlist: {symbols[:5]}...")
        
        if not symbols:
            print("⚠️ No symbols found in watchlist")
            return False
        
        # Test LTP collection for first few symbols
        test_symbols = symbols[:3]  # Test with first 3 symbols
        print(f"📊 Testing LTP collection for: {test_symbols}")
        
        ltp_data = angelone_client.get_ltp_data(test_symbols)
        
        if ltp_data:
            print(f"✅ LTP collection successful!")
            for symbol, ltp in ltp_data.items():
                print(f"   {symbol}: ₹{ltp}")
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
        # Test full LTP collection
        print("📊 Testing full LTP collection...")
        ltp_data = ltp_service.collect_ltp_data()
        
        if ltp_data:
            print(f"✅ LTP service successful! Collected data for {len(ltp_data)} symbols")
            
            # Test data retrieval
            print("📖 Testing data retrieval...")
            symbols = list(ltp_data.keys())
            if symbols:
                test_symbol = symbols[0].replace('-EQ', '')  # Convert back to Upstox format
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
        symbols = ltp_service.get_watchlist_symbols()
        if not symbols:
            print("⚠️ No symbols found for backfill test")
            return False
        
        test_symbol = symbols[0].replace('-EQ', '')  # Convert to Upstox format
        print(f"🔍 Testing backfill for: {test_symbol}")
        
        # Check missing data
        missing_ranges = backfill_service.detect_missing_data(test_symbol, days_back=7)
        print(f"📊 Found {len(missing_ranges)} missing data ranges")
        
        if missing_ranges:
            print("📅 Missing ranges:")
            for start, end in missing_ranges:
                print(f"   {start} to {end}")
        
        # Test backfill (but don't actually run it to avoid API limits)
        print("🔄 Testing backfill logic (dry run)...")
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
        print(f"🔌 AngelOne connected: {status['angelone_connected']}")
        
        if status['next_jobs']:
            print("📅 Scheduled jobs:")
            for job in status['next_jobs'][:3]:  # Show first 3
                print(f"   {job['job']}: {job['next_run']}")
        
        print("✅ Scheduler status check completed")
        return True
        
    except Exception as e:
        print(f"❌ Scheduler status test error: {e}")
        return False

def run_all_tests():
    """Run all data fetching tests."""
    print("🧪 STARTING DATA FETCH TESTS")
    print("="*60)
    
    tests = [
        ("AngelOne Connection", test_angelone_connection),
        ("LTP Collection", test_ltp_collection),
        ("LTP Service", test_ltp_service),
        ("Backfill Service", test_backfill_service),
        ("Data Freshness", test_data_freshness),
        ("Scheduler Status", test_scheduler_status),
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
        print("🎉 All tests passed! Data fetching system is ready.")
    else:
        print("⚠️ Some tests failed. Please check the configuration.")
    
    return passed == total

if __name__ == "__main__":
    print("🚀 AngelOne Data Fetching Test Suite")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("app"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Run tests
    success = run_all_tests()
    
    if success:
        print("\n🎉 All systems go! You can now start the data scheduler.")
        print("💡 To start data collection: python -c 'from data_fetch.data_scheduler import data_scheduler; data_scheduler.start()'")
    else:
        print("\n🔧 Please fix the failing tests before proceeding.")
    
    sys.exit(0 if success else 1)
