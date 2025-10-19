#!/usr/bin/env python3
"""
Test all fixes: PostgreSQL + Upstox API
"""

import os
import sys
from dotenv import load_dotenv

def test_postgresql():
    """Test PostgreSQL connection."""
    print("🗄️ TESTING POSTGRESQL")
    print("-" * 40)
    
    try:
        from app.db import DATABASE_URL, engine, SessionLocal
        print(f"📊 Database URL: {DATABASE_URL}")
        
        if 'postgresql' in DATABASE_URL:
            print("✅ Using PostgreSQL")
        else:
            print("❌ Still using SQLite")
            return False
        
        # Test connection
        with engine.connect() as conn:
            print("✅ PostgreSQL connection successful!")
        
        # Test session
        db = SessionLocal()
        try:
            print("✅ Database session created!")
        finally:
            db.close()
        
        # Create tables
        from app.models import Base
        Base.metadata.create_all(bind=engine)
        print("✅ PostgreSQL tables created!")
        
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL test failed: {e}")
        return False

def test_upstox_api():
    """Test Upstox API."""
    print("\n🌐 TESTING UPSTOX API")
    print("-" * 40)
    
    try:
        load_dotenv()
        token = os.getenv('UPSTOX_ACCESS_TOKEN')
        print(f"📊 Token: {token[:20]}..." if token else "❌ No token")
        
        # Test connection
        sys.path.append('data-fetch')
        from upstox_ltp_client import upstox_ltp_client
        
        if upstox_ltp_client.test_connection():
            print("✅ Upstox API authentication successful!")
            return True
        else:
            print("❌ Upstox API authentication failed")
            print("💡 Please update UPSTOX_ACCESS_TOKEN in .env file")
            return False
            
    except Exception as e:
        print(f"❌ Upstox API test error: {e}")
        return False

def test_ltp_api():
    """Test LTP API."""
    print("\n📊 TESTING LTP API")
    print("-" * 40)
    
    try:
        sys.path.append('data-fetch')
        from ltp_service import ltp_service
        
        print("🚀 Testing LTP collection...")
        ltp_data = ltp_service.collect_ltp_data()
        
        if ltp_data:
            print(f"✅ LTP API Success: {len(ltp_data)} stocks")
            
            # Show sample data
            sample_symbols = list(ltp_data.keys())[:3]
            for symbol in sample_symbols:
                print(f"   💰 {symbol}: ₹{ltp_data[symbol]}")
            
            return True
        else:
            print("❌ LTP API failed - no data received")
            return False
            
    except Exception as e:
        print(f"❌ LTP API test error: {e}")
        return False

def test_history_api():
    """Test History API."""
    print("\n📈 TESTING HISTORY API")
    print("-" * 40)
    
    try:
        sys.path.append('data-fetch')
        from upstox_client import upstox_client
        from datetime import date, timedelta
        
        # Test with TCS data
        end_date = date.today()
        start_date = end_date - timedelta(days=1)
        
        print(f"🧪 Fetching TCS data from {start_date} to {end_date}")
        
        candles = upstox_client.get_historical_data(
            instrument_key='NSE_EQ|INE467B01029',  # TCS
            interval='1minute',
            from_date=start_date,
            to_date=end_date
        )
        
        if candles:
            print(f"✅ History API Success: {len(candles)} candles")
            return True
        else:
            print("❌ History API failed - no data received")
            return False
            
    except Exception as e:
        print(f"❌ History API test error: {e}")
        return False

def test_complete_system():
    """Test complete system."""
    print("\n🎯 TESTING COMPLETE SYSTEM")
    print("-" * 40)
    
    try:
        # Test FastAPI app
        from app.main import app
        print("✅ FastAPI app loads successfully")
        
        # Test alert system
        from app.scheduler import check_for_alerts
        print("✅ Alert system ready")
        
        # Test data scheduler
        sys.path.append('data-fetch')
        from data_scheduler import data_scheduler
        print("✅ Data scheduler ready")
        
        return True
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 TESTING ALL FIXES")
    print("=" * 60)
    
    results = {}
    
    # Test PostgreSQL
    results['postgresql'] = test_postgresql()
    
    # Test Upstox API
    results['upstox_api'] = test_upstox_api()
    
    # Test LTP API (only if Upstox works)
    if results['upstox_api']:
        results['ltp_api'] = test_ltp_api()
    else:
        results['ltp_api'] = False
    
    # Test History API (only if Upstox works)
    if results['upstox_api']:
        results['history_api'] = test_history_api()
    else:
        results['history_api'] = False
    
    # Test complete system
    results['system'] = test_complete_system()
    
    # Summary
    print("\n🎯 TEST RESULTS")
    print("=" * 60)
    
    for component, success in results.items():
        status = "✅ WORKING" if success else "❌ NEEDS FIX"
        print(f"   {component.upper().replace('_', ' ')}: {status}")
    
    total_working = sum(results.values())
    total_tests = len(results)
    
    print(f"\n📊 OVERALL: {total_working}/{total_tests} components working")
    
    if total_working == total_tests:
        print("🎉 ALL FIXES SUCCESSFUL!")
        print("🚀 System is ready for production!")
    elif total_working >= 3:
        print("⚠️ MOSTLY WORKING - Minor issues remain")
    else:
        print("❌ MAJOR ISSUES - Need manual intervention")
    
    # Next steps
    print("\n💡 NEXT STEPS:")
    
    if not results['postgresql']:
        print("   🗄️ Fix PostgreSQL: Check installation and .env configuration")
    
    if not results['upstox_api']:
        print("   🌐 Fix Upstox API: Get new access token from https://developer.upstox.com/")
    
    if results['postgresql'] and results['upstox_api']:
        print("   🎉 Start the application:")
        print("   🚀 python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    main()
