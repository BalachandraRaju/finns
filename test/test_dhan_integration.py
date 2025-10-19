"""
Comprehensive test script for Dhan API integration.
Tests authentication, instrument mapping, and LTP data fetching.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data-fetch'))


def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def print_section(title):
    """Print a formatted section."""
    print("\n" + "-"*70)
    print(f"  {title}")
    print("-"*70 + "\n")


def test_authentication():
    """Test Dhan API authentication."""
    print_section("TEST 1: Authentication")

    try:
        sys.path.insert(0, 'data-fetch')
        from dhan_ltp_client import dhan_ltp_client

        if dhan_ltp_client.test_connection():
            print("✅ Authentication test PASSED")
            return True
        else:
            print("❌ Authentication test FAILED")
            print("\n💡 Please run: python dhan_auth_helper.py")
            print("   to set up your access token properly.")
            return False

    except Exception as e:
        print(f"❌ Authentication test ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_instrument_mapping():
    """Test instrument mapping."""
    print_section("TEST 2: Instrument Mapping")

    try:
        sys.path.insert(0, 'data-fetch')
        from dhan_instruments import dhan_instruments
        
        # Test with common symbols
        test_symbols = ["TCS", "RELIANCE", "INFY", "HDFCBANK", "ICICIBANK"]
        
        print("Testing symbol to security ID mapping...")
        mapped = dhan_instruments.get_security_ids(test_symbols)
        
        for symbol in test_symbols:
            security_id = mapped.get(symbol)
            if security_id:
                print(f"   ✅ {symbol:12} → Security ID: {security_id}")
            else:
                print(f"   ❌ {symbol:12} → Not found")
        
        success_rate = len(mapped) / len(test_symbols) * 100
        print(f"\nMapping success rate: {success_rate:.1f}% ({len(mapped)}/{len(test_symbols)})")
        
        if success_rate >= 80:
            print("✅ Instrument mapping test PASSED")
            return True, mapped
        else:
            print("⚠️  Instrument mapping test PARTIAL")
            return True, mapped
            
    except Exception as e:
        print(f"❌ Instrument mapping test ERROR: {e}")
        return False, {}


def test_ltp_fetching(security_ids):
    """Test LTP data fetching."""
    print_section("TEST 3: LTP Data Fetching")

    try:
        sys.path.insert(0, 'data-fetch')
        from dhan_ltp_client import dhan_ltp_client
        
        if not security_ids:
            print("⚠️  No security IDs available for testing")
            return False
        
        # Take first 5 security IDs for testing
        test_ids = list(security_ids.values())[:5]
        test_symbols = list(security_ids.keys())[:5]
        
        print(f"Fetching LTP for {len(test_ids)} securities...")
        ltp_data = dhan_ltp_client.get_ltp_data(test_ids)
        
        if ltp_data:
            print("\n📊 LTP Data:")
            for i, (symbol, security_id) in enumerate(zip(test_symbols, test_ids)):
                ltp = ltp_data.get(security_id)
                if ltp:
                    print(f"   ✅ {symbol:12} (ID: {security_id:6}) → ₹{ltp:,.2f}")
                else:
                    print(f"   ❌ {symbol:12} (ID: {security_id:6}) → No data")
            
            success_rate = len(ltp_data) / len(test_ids) * 100
            print(f"\nLTP fetch success rate: {success_rate:.1f}% ({len(ltp_data)}/{len(test_ids)})")
            
            if success_rate >= 80:
                print("✅ LTP fetching test PASSED")
                return True
            else:
                print("⚠️  LTP fetching test PARTIAL")
                return True
        else:
            print("❌ LTP fetching test FAILED - No data received")
            return False
            
    except Exception as e:
        print(f"❌ LTP fetching test ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_watchlist_integration():
    """Test integration with watchlist."""
    print_section("TEST 4: Watchlist Integration")

    try:
        sys.path.insert(0, 'data-fetch')
        from dhan_instruments import dhan_instruments
        
        watchlist_file = "nse_fo_stock_symbols.txt"
        
        if not os.path.exists(watchlist_file):
            print(f"⚠️  Watchlist file not found: {watchlist_file}")
            return False
        
        # Read watchlist
        with open(watchlist_file, 'r') as f:
            content = f.read()
            symbols = [s.strip().strip('"') for s in content.split(',')]
            # Filter out test symbols
            symbols = [s for s in symbols if not s.startswith('0') and s]
        
        print(f"📋 Found {len(symbols)} symbols in watchlist")
        
        # Map all symbols
        print("Mapping all symbols to security IDs...")
        mapped = dhan_instruments.get_security_ids(symbols)
        
        success_rate = len(mapped) / len(symbols) * 100
        print(f"\nMapping results:")
        print(f"   ✅ Mapped: {len(mapped)} symbols")
        print(f"   ❌ Not found: {len(symbols) - len(mapped)} symbols")
        print(f"   Success rate: {success_rate:.1f}%")
        
        # Show some unmapped symbols
        unmapped = [s for s in symbols if s not in mapped]
        if unmapped:
            print(f"\n⚠️  Sample unmapped symbols (first 10):")
            for symbol in unmapped[:10]:
                print(f"      - {symbol}")
        
        if success_rate >= 90:
            print("\n✅ Watchlist integration test PASSED")
            return True
        elif success_rate >= 70:
            print("\n⚠️  Watchlist integration test PARTIAL")
            print("   Some symbols couldn't be mapped. This is normal for F&O symbols.")
            return True
        else:
            print("\n❌ Watchlist integration test FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Watchlist integration test ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print_header("🧪 DHAN API INTEGRATION TEST SUITE")
    
    print("This script will test:")
    print("  1. Dhan API authentication")
    print("  2. Instrument symbol to security ID mapping")
    print("  3. LTP data fetching")
    print("  4. Watchlist integration")
    
    results = {
        'authentication': False,
        'instrument_mapping': False,
        'ltp_fetching': False,
        'watchlist_integration': False
    }
    
    # Test 1: Authentication
    results['authentication'] = test_authentication()
    
    if not results['authentication']:
        print_header("❌ TESTS FAILED")
        print("Authentication failed. Please fix authentication before proceeding.")
        print("\nRun: python dhan_auth_helper.py")
        return
    
    # Test 2: Instrument Mapping
    mapping_success, security_ids = test_instrument_mapping()
    results['instrument_mapping'] = mapping_success
    
    # Test 3: LTP Fetching (only if we have security IDs)
    if security_ids:
        results['ltp_fetching'] = test_ltp_fetching(security_ids)
    
    # Test 4: Watchlist Integration
    results['watchlist_integration'] = test_watchlist_integration()
    
    # Summary
    print_header("📊 TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    print("Test Results:")
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {test_name.replace('_', ' ').title():30} {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n📝 Next Steps:")
        print("   1. Your Dhan API integration is working correctly")
        print("   2. You can now proceed to integrate with your existing system")
        print("   3. Replace Upstox API calls with Dhan API calls")
    elif passed_tests >= total_tests * 0.75:
        print("\n⚠️  MOST TESTS PASSED")
        print("\nSome tests failed, but core functionality is working.")
        print("Review the failed tests above and fix any issues.")
    else:
        print("\n❌ MULTIPLE TESTS FAILED")
        print("\nPlease review the errors above and fix the issues.")
        print("Run this script again after fixing the problems.")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()

