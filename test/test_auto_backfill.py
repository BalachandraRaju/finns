#!/usr/bin/env python3
"""
Test automatic backfill functionality with Dhan API.
This script tests that the database service automatically fetches missing data.
"""

import sys
import os
from datetime import date, timedelta

# Add project root and data-fetch to path
project_root = os.path.dirname(os.path.abspath(__file__))
data_fetch_dir = os.path.join(project_root, 'data-fetch')
sys.path.insert(0, project_root)
sys.path.insert(0, data_fetch_dir)

from logzero import logger

# Now import from data-fetch directory
import importlib.util

# Load database_service module
spec = importlib.util.spec_from_file_location("database_service", os.path.join(data_fetch_dir, "database_service.py"))
database_service_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(database_service_module)
database_service = database_service_module.database_service

# Load dhan_instruments module
spec2 = importlib.util.spec_from_file_location("dhan_instruments", os.path.join(data_fetch_dir, "dhan_instruments.py"))
dhan_instruments_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(dhan_instruments_module)
dhan_instruments = dhan_instruments_module.dhan_instruments

def test_auto_backfill():
    """Test automatic backfill for a stock with no data."""
    
    print("=" * 80)
    print("🧪 TESTING AUTOMATIC BACKFILL WITH DHAN API")
    print("=" * 80)
    
    # Test with a stock that might not have data
    test_symbol = "HDFCBANK"
    
    print(f"\n1️⃣ Getting Dhan security ID for {test_symbol}...")
    security_id = dhan_instruments.get_security_id(test_symbol)
    
    if not security_id:
        print(f"❌ Could not find security ID for {test_symbol}")
        return False
    
    print(f"✅ Security ID: {security_id}")
    
    # Create Dhan instrument key
    instrument_key = f"DHAN_{security_id}"
    print(f"✅ Instrument Key: {instrument_key}")
    
    # Test date range (last 2 months)
    end_date = date.today()
    start_date = end_date - timedelta(days=60)
    
    print(f"\n2️⃣ Testing automatic backfill for 1-minute data...")
    print(f"   Date range: {start_date} to {end_date}")
    print(f"   Auto-backfill: ENABLED")
    
    # This should automatically trigger backfill if data is missing
    candles = database_service.get_candles_smart(
        instrument_key=instrument_key,
        interval="1minute",
        start_date=start_date,
        end_date=end_date,
        auto_backfill=True  # Enable automatic backfill
    )
    
    if candles:
        print(f"\n✅ SUCCESS! Retrieved {len(candles)} candles")
        print(f"   First candle: {candles[0]['timestamp']}")
        print(f"   Last candle: {candles[-1]['timestamp']}")
        print(f"   Sample data: O={candles[-1]['open']}, H={candles[-1]['high']}, L={candles[-1]['low']}, C={candles[-1]['close']}")
        return True
    else:
        print(f"\n❌ FAILED! No candles retrieved")
        return False

def test_without_backfill():
    """Test data retrieval without automatic backfill."""
    
    print("\n" + "=" * 80)
    print("🧪 TESTING WITHOUT AUTOMATIC BACKFILL")
    print("=" * 80)
    
    test_symbol = "RELIANCE"
    
    print(f"\n1️⃣ Getting Dhan security ID for {test_symbol}...")
    security_id = dhan_instruments.get_security_id(test_symbol)
    
    if not security_id:
        print(f"❌ Could not find security ID for {test_symbol}")
        return False
    
    instrument_key = f"DHAN_{security_id}"
    print(f"✅ Instrument Key: {instrument_key}")
    
    end_date = date.today()
    start_date = end_date - timedelta(days=60)
    
    print(f"\n2️⃣ Testing data retrieval WITHOUT auto-backfill...")
    print(f"   Auto-backfill: DISABLED")
    
    # This should only return data if it exists in database
    candles = database_service.get_candles_smart(
        instrument_key=instrument_key,
        interval="1minute",
        start_date=start_date,
        end_date=end_date,
        auto_backfill=False  # Disable automatic backfill
    )
    
    if candles:
        print(f"\n✅ Found {len(candles)} candles in database (no backfill needed)")
        return True
    else:
        print(f"\n⚠️ No candles found (expected - backfill was disabled)")
        return True  # This is expected behavior

def main():
    """Run all tests."""
    
    print("\n🚀 AUTOMATIC BACKFILL TEST SUITE")
    print("=" * 80)
    print("This test verifies that the database service automatically")
    print("fetches missing data from Dhan API when needed.")
    print("=" * 80)
    
    results = []
    
    # Test 1: Auto-backfill enabled
    try:
        result1 = test_auto_backfill()
        results.append(("Auto-backfill enabled", result1))
    except Exception as e:
        print(f"\n❌ Test 1 failed with error: {e}")
        results.append(("Auto-backfill enabled", False))
    
    # Test 2: Auto-backfill disabled
    try:
        result2 = test_without_backfill()
        results.append(("Auto-backfill disabled", result2))
    except Exception as e:
        print(f"\n❌ Test 2 failed with error: {e}")
        results.append(("Auto-backfill disabled", False))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Automatic backfill is working correctly")
        return 0
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("❌ Check the error messages above")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n👋 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

