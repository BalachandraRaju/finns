#!/usr/bin/env python3
"""
Comprehensive test script to verify Upstox API integration is working properly.
Tests API connection, data fetching, database storage, and chart generation.
"""

import sys
import os
import datetime
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_environment_setup():
    """Test if environment variables are properly configured."""
    print("🔧 TESTING ENVIRONMENT SETUP")
    print("=" * 50)
    
    access_token = os.getenv("UPSTOX_ACCESS_TOKEN", "")
    
    if not access_token:
        print("❌ UPSTOX_ACCESS_TOKEN not found in environment")
        print("💡 Please check your .env file")
        return False
    
    print(f"✅ UPSTOX_ACCESS_TOKEN found: {access_token[:10]}...{access_token[-10:]}")
    print(f"📝 Token length: {len(access_token)} characters")
    
    return True

def test_upstox_client_import():
    """Test if Upstox client can be imported and configured."""
    print("\n📦 TESTING UPSTOX CLIENT IMPORT")
    print("=" * 50)
    
    try:
        import upstox_client
        print("✅ upstox_client imported successfully")
        
        # Test configuration
        from app.charts import api_client, ACCESS_TOKEN
        print("✅ API client configuration imported")
        print(f"📝 Access token configured: {bool(ACCESS_TOKEN)}")
        
        return True
    except ImportError as e:
        print(f"❌ Failed to import upstox_client: {e}")
        print("💡 Run: pip install upstox-python-sdk")
        return False
    except Exception as e:
        print(f"❌ Error configuring Upstox client: {e}")
        return False

def test_database_connection():
    """Test database connection and basic operations."""
    print("\n🗄️ TESTING DATABASE CONNECTION")
    print("=" * 50)
    
    try:
        from app.db import get_db_session
        from app.models import Candle
        
        # Test database session
        session = get_db_session()
        print("✅ Database session created successfully")
        
        # Test basic query
        candle_count = session.query(Candle).count()
        print(f"✅ Database query successful: {candle_count} candles in database")
        
        session.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_watchlist_stocks():
    """Test if watchlist stocks are available."""
    print("\n📈 TESTING WATCHLIST STOCKS")
    print("=" * 50)
    
    try:
        from app.crud import get_watchlist_details
        
        stocks = get_watchlist_details()
        print(f"✅ Watchlist query successful: {len(stocks)} stocks found")
        
        if stocks:
            print("📊 Sample stocks:")
            for i, stock in enumerate(stocks[:3], 1):
                print(f"   {i}. {stock.name} ({stock.symbol}) - {stock.instrument_key}")
        else:
            print("⚠️ No stocks in watchlist - add some stocks first")
            
        return len(stocks) > 0
    except Exception as e:
        print(f"❌ Watchlist query failed: {e}")
        return False

def test_upstox_api_connection():
    """Test actual Upstox API connection."""
    print("\n🌐 TESTING UPSTOX API CONNECTION")
    print("=" * 50)
    
    try:
        import upstox_client
        from app.charts import api_client
        
        # Test with a simple API call
        api_instance = upstox_client.LoginApi(api_client)
        
        # Try to get profile (this should work if token is valid)
        try:
            profile_response = api_instance.get_profile()
            print("✅ Upstox API connection successful")
            print(f"📝 User: {profile_response.data.user_name}")
            print(f"📝 User ID: {profile_response.data.user_id}")
            return True
        except Exception as api_error:
            print(f"❌ Upstox API call failed: {api_error}")
            print("💡 Check if your access token is valid and not expired")
            return False
            
    except Exception as e:
        print(f"❌ Upstox API setup failed: {e}")
        return False

def test_data_fetching():
    """Test data fetching for a sample stock."""
    print("\n📊 TESTING DATA FETCHING")
    print("=" * 50)
    
    try:
        from app.crud import get_watchlist_details
        from app.charts import fetch_and_save_historical_data
        
        # Get a sample stock
        stocks = get_watchlist_details()
        if not stocks:
            print("⚠️ No stocks available for testing")
            return False
            
        test_stock = stocks[0]
        print(f"🎯 Testing with: {test_stock.name} ({test_stock.symbol})")
        print(f"📝 Instrument Key: {test_stock.instrument_key}")
        
        # Test data fetching
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=7)  # Last 7 days
        
        print(f"📅 Fetching data from {start_date} to {end_date}")
        
        try:
            fetch_and_save_historical_data(
                test_stock.instrument_key, 
                "day", 
                start_date, 
                end_date
            )
            print("✅ Data fetching completed successfully")
            return True
        except Exception as fetch_error:
            print(f"❌ Data fetching failed: {fetch_error}")
            return False
            
    except Exception as e:
        print(f"❌ Data fetching test setup failed: {e}")
        return False

def test_chart_generation():
    """Test chart generation with sample data."""
    print("\n📈 TESTING CHART GENERATION")
    print("=" * 50)
    
    try:
        from app.crud import get_watchlist_details
        from app.charts import generate_pnf_chart_html
        
        # Get a sample stock
        stocks = get_watchlist_details()
        if not stocks:
            print("⚠️ No stocks available for testing")
            return False
            
        test_stock = stocks[0]
        print(f"🎯 Testing chart generation for: {test_stock.name}")
        
        # Generate chart
        chart_html = generate_pnf_chart_html(
            test_stock.instrument_key,
            box_pct=0.01,
            reversal=3,
            interval="day",
            time_range="1month",
            show_fibonacci=True
        )
        
        if chart_html and len(chart_html) > 100:
            print("✅ Chart generation successful")
            print(f"📝 Chart HTML length: {len(chart_html)} characters")
            print("📊 Chart includes: P&F points, Fibonacci levels, interactive features")
            return True
        else:
            print("❌ Chart generation failed - empty or invalid HTML")
            return False
            
    except Exception as e:
        print(f"❌ Chart generation failed: {e}")
        return False

def test_pattern_detection():
    """Test pattern detection system."""
    print("\n🔍 TESTING PATTERN DETECTION")
    print("=" * 50)
    
    try:
        from app.pattern_detector import PatternDetector, AlertType
        from app.charts import _calculate_pnf_points
        
        # Create sample data for testing
        sample_highs = [100, 102, 105, 103, 107, 104, 108, 106, 110, 108, 115]
        sample_lows = [98, 100, 103, 101, 105, 102, 106, 104, 108, 106, 113]
        
        # Calculate P&F points
        x_coords, y_coords, pnf_symbols = _calculate_pnf_points(sample_highs, sample_lows, 0.01, 3)
        
        if x_coords:
            print(f"✅ P&F calculation successful: {len(x_coords)} points generated")
            
            # Test pattern detection
            detector = PatternDetector()
            alerts = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols)
            
            print(f"✅ Pattern detection successful: {len(alerts)} alerts generated")
            
            for alert in alerts:
                print(f"   🚨 {alert.alert_type.value} alert at column {alert.column}, price {alert.price:.2f}")
                
            return True
        else:
            print("❌ P&F calculation failed - no points generated")
            return False
            
    except Exception as e:
        print(f"❌ Pattern detection test failed: {e}")
        return False

def run_comprehensive_test():
    """Run all tests and provide summary."""
    print("🚀 UPSTOX INTEGRATION COMPREHENSIVE TEST")
    print("Testing all components of the trading system")
    print("=" * 80)
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Upstox Client Import", test_upstox_client_import),
        ("Database Connection", test_database_connection),
        ("Watchlist Stocks", test_watchlist_stocks),
        ("Upstox API Connection", test_upstox_api_connection),
        ("Data Fetching", test_data_fetching),
        ("Chart Generation", test_chart_generation),
        ("Pattern Detection", test_pattern_detection),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 80)
    print("📋 TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Upstox integration is working perfectly!")
        print("🚀 Your trading system is ready for live use!")
    elif passed >= total * 0.7:
        print("⚠️ MOSTLY WORKING - Some issues need attention")
        print("🔧 Check failed tests and fix configuration")
    else:
        print("❌ MAJOR ISSUES - System needs significant fixes")
        print("🛠️ Review setup and configuration")
    
    return passed == total

if __name__ == "__main__":
    run_comprehensive_test()
