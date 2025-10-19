#!/usr/bin/env python3
"""
Quick test to check if Upstox integration basics are working.
"""

import sys
import os
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def quick_test():
    """Run a quick test of basic functionality."""
    print("🚀 QUICK UPSTOX INTEGRATION TEST")
    print("=" * 50)
    
    # Test 1: Environment
    print("1. 🔧 Testing Environment...")
    access_token = os.getenv("UPSTOX_ACCESS_TOKEN", "")
    if access_token:
        print(f"   ✅ Access token found: {access_token[:10]}...{access_token[-10:]}")
    else:
        print("   ❌ No access token found")
        return False
    
    # Test 2: Imports
    print("2. 📦 Testing Imports...")
    try:
        import upstox_client
        from app.charts import generate_pnf_chart_html
        from app.crud import get_watchlist_details
        print("   ✅ All imports successful")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Test 3: Database
    print("3. 🗄️ Testing Database...")
    try:
        stocks = get_watchlist_details()
        print(f"   ✅ Database working: {len(stocks)} stocks found")
        if stocks:
            print(f"   📊 Sample: {stocks[0].name} ({stocks[0].symbol})")
    except Exception as e:
        print(f"   ❌ Database failed: {e}")
        return False
    
    # Test 4: API Client
    print("4. 🌐 Testing API Client...")
    try:
        from app.charts import api_client
        api_instance = upstox_client.LoginApi(api_client)
        profile = api_instance.get_profile()
        print(f"   ✅ API working: User {profile.data.user_name}")
    except Exception as e:
        print(f"   ❌ API failed: {e}")
        print("   💡 Check if access token is valid")
        return False
    
    # Test 5: Chart Generation
    print("5. 📈 Testing Chart Generation...")
    try:
        if stocks:
            chart_html = generate_pnf_chart_html(
                stocks[0].instrument_key,
                box_pct=0.01,
                reversal=3,
                show_fibonacci=True
            )
            if chart_html and len(chart_html) > 100:
                print(f"   ✅ Chart generated: {len(chart_html)} chars")
            else:
                print("   ❌ Chart generation failed")
                return False
        else:
            print("   ⚠️ No stocks to test chart generation")
    except Exception as e:
        print(f"   ❌ Chart generation failed: {e}")
        return False
    
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ Upstox integration is working correctly!")
    return True

if __name__ == "__main__":
    success = quick_test()
    if not success:
        print("\n❌ Some tests failed. Check configuration.")
        sys.exit(1)
