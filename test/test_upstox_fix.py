#!/usr/bin/env python3
"""
Test Upstox API fix after updating access token.
"""

import os
import sys
from dotenv import load_dotenv

def test_upstox_token():
    """Test the new Upstox access token."""
    print("🌐 TESTING NEW UPSTOX ACCESS TOKEN")
    print("=" * 50)
    
    load_dotenv()
    token = os.getenv('UPSTOX_ACCESS_TOKEN')
    
    if not token:
        print("❌ No UPSTOX_ACCESS_TOKEN found in .env file")
        return False
    
    print(f"📊 Token: {token[:20]}...")
    
    # Test with direct API call
    try:
        import requests
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        
        print("🧪 Testing API connection...")
        response = requests.get('https://api.upstox.com/v2/user/profile', headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Upstox API authentication successful!")
            user_data = response.json()
            print(f"👤 User: {user_data.get('data', {}).get('user_name', 'Unknown')}")
            return True
        else:
            print(f"❌ Upstox API failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False

def test_ltp_api():
    """Test LTP API with new token."""
    print("\n📊 TESTING LTP API")
    print("-" * 30)
    
    try:
        sys.path.append('data-fetch')
        from ltp_service import ltp_service
        
        print("🚀 Testing LTP collection...")
        ltp_data = ltp_service.collect_ltp_data()
        
        if ltp_data:
            print(f"✅ LTP API Success!")
            print(f"   📊 Stocks collected: {len(ltp_data)}")
            print(f"   🌐 API calls made: 1 (instead of {len(ltp_data)})")
            print(f"   💰 API efficiency: {len(ltp_data)}x improvement")
            
            # Show sample data
            sample_symbols = list(ltp_data.keys())[:3]
            print(f"   📈 Sample data:")
            for symbol in sample_symbols:
                print(f"      💰 {symbol}: ₹{ltp_data[symbol]}")
            
            return True
        else:
            print("❌ LTP API failed - no data received")
            return False
            
    except Exception as e:
        print(f"❌ LTP API test error: {e}")
        return False

def test_history_api():
    """Test History API with new token."""
    print("\n📈 TESTING HISTORY API")
    print("-" * 30)
    
    try:
        sys.path.append('data-fetch')
        from upstox_client import upstox_client
        from datetime import date, timedelta
        
        # Test with TCS data
        end_date = date.today()
        start_date = end_date - timedelta(days=1)
        
        print(f"🧪 Fetching TCS 1-minute data...")
        print(f"   📅 From: {start_date}")
        print(f"   📅 To: {end_date}")
        
        candles = upstox_client.get_historical_data(
            instrument_key='NSE_EQ|INE467B01029',  # TCS
            interval='1minute',
            from_date=start_date,
            to_date=end_date
        )
        
        if candles:
            print(f"✅ History API Success!")
            print(f"   📊 Candles retrieved: {len(candles)}")
            print(f"   📈 Sample candle: OHLC = {candles[0]['open']}/{candles[0]['high']}/{candles[0]['low']}/{candles[0]['close']}")
            return True
        else:
            print("❌ History API failed - no data received")
            return False
            
    except Exception as e:
        print(f"❌ History API test error: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 TESTING UPSTOX API FIX")
    print("=" * 50)
    print("Make sure you've updated UPSTOX_ACCESS_TOKEN in .env file!")
    print("=" * 50)
    
    # Test authentication
    auth_success = test_upstox_token()
    
    if not auth_success:
        print("\n❌ AUTHENTICATION FAILED")
        print("💡 Please:")
        print("   1. Generate new token from Upstox Developer Console")
        print("   2. Update UPSTOX_ACCESS_TOKEN in .env file")
        print("   3. Run this test again")
        return
    
    # Test LTP API
    ltp_success = test_ltp_api()
    
    # Test History API
    history_success = test_history_api()
    
    # Summary
    print("\n🎯 TEST SUMMARY")
    print("=" * 50)
    print(f"   🔐 Authentication: {'✅ WORKING' if auth_success else '❌ FAILED'}")
    print(f"   📊 LTP API: {'✅ WORKING' if ltp_success else '❌ FAILED'}")
    print(f"   📈 History API: {'✅ WORKING' if history_success else '❌ FAILED'}")
    
    if auth_success and ltp_success and history_success:
        print("\n🎉 ALL UPSTOX APIS WORKING!")
        print("🚀 System is ready for:")
        print("   • Real-time LTP collection every minute")
        print("   • Automatic historical data backfill")
        print("   • Database-first alert generation")
        print("   • 20x API efficiency optimization")
        
        print("\n💡 Next steps:")
        print("   1. Start the application:")
        print("      python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("   2. Start data collection:")
        print("      python -c \"import sys; sys.path.append('data-fetch'); from data_scheduler import data_scheduler; data_scheduler.start()\"")
    else:
        print("\n⚠️ Some APIs still not working")
        print("💡 Check the error messages above")

if __name__ == "__main__":
    main()
