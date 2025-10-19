#!/usr/bin/env python3
"""
Test script to diagnose issues with specific instrument NSE_EQ|INE335Y01020.
"""

import sys
import os
import datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import charts, crud

def test_specific_instrument():
    """Test the problematic instrument NSE_EQ|INE335Y01020."""
    print("🔍 Testing Specific Instrument: NSE_EQ|INE335Y01020")
    print("=" * 60)
    
    instrument_key = "NSE_EQ|INE335Y01020"
    
    # First, check if this stock is in our database
    print(f"📊 Checking stock info in database...")
    stock_info = crud.get_stock_by_instrument_key(instrument_key)
    
    if stock_info:
        print(f"   ✅ Stock found: {stock_info['symbol']} - {stock_info['name']}")
    else:
        print(f"   ❌ Stock not found in database")
        print(f"   💡 This might be why charts aren't working")
        return
    
    # Test data fetching
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=3)
    
    print(f"\n📅 Testing data fetching from {start_date} to {today}")
    
    try:
        # Test 1-minute data fetching
        candles = charts.get_candles_for_instrument(instrument_key, "1minute", start_date, today)
        print(f"   📊 Retrieved {len(candles)} 1-minute candles")
        
        if candles:
            latest = candles[-1]
            earliest = candles[0]
            print(f"   📈 Latest: {latest['timestamp']} - Close: {latest['close']}")
            print(f"   📉 Earliest: {earliest['timestamp']} - Close: {earliest['close']}")
            
            # Check today's data specifically
            today_candles = [c for c in candles if str(today) in str(c['timestamp'])]
            print(f"   🕐 Today's candles: {len(today_candles)}")
            
        else:
            print(f"   ❌ No candles retrieved")
            
    except Exception as e:
        print(f"   ❌ Error fetching data: {e}")
    
    # Test chart generation
    print(f"\n📊 Testing chart generation...")
    
    try:
        # Test with different box sizes
        box_sizes = [0.001, 0.0025, 0.005, 0.01]
        
        for box_size in box_sizes:
            chart_html = charts.generate_pnf_chart_html(
                instrument_key, 
                box_pct=box_size, 
                interval="1minute", 
                time_range="1month"
            )
            
            if chart_html and "Could not find" not in chart_html:
                print(f"   ✅ Chart generated with {box_size*100:.2f}% box: {len(chart_html)} chars")
                
                # Check for data
                if '"x":[]' in chart_html or '"y":[]' in chart_html:
                    print(f"      ❌ Empty data arrays")
                elif '"x":[' in chart_html and '"y":[' in chart_html:
                    print(f"      ✅ Contains chart data")
                else:
                    print(f"      ⚠️ Data status unclear")
            else:
                print(f"   ❌ Chart generation failed with {box_size*100:.2f}% box")
                if chart_html:
                    print(f"      Error: {chart_html[:100]}...")
                    
    except Exception as e:
        print(f"   ❌ Chart generation error: {e}")

def test_database_data():
    """Check what's in the database for this instrument."""
    print(f"\n💾 Testing Database Data for NSE_EQ|INE335Y01020")
    print("=" * 50)
    
    from app.db import SessionLocal
    from app.models import Candle
    from sqlalchemy import func, desc
    
    db_session = SessionLocal()
    
    try:
        instrument_key = "NSE_EQ|INE335Y01020"
        today = datetime.date.today()
        
        # Check total 1-minute candles
        total_1min = db_session.query(Candle).filter(
            Candle.instrument_key == instrument_key,
            Candle.interval == "1minute"
        ).count()
        
        print(f"📊 Total 1-minute candles in DB: {total_1min}")
        
        # Check today's 1-minute candles
        today_1min = db_session.query(Candle).filter(
            Candle.instrument_key == instrument_key,
            Candle.interval == "1minute",
            func.date(Candle.timestamp) == today
        ).count()
        
        print(f"🕐 Today's 1-minute candles: {today_1min}")
        
        # Get latest candle
        latest_candle = db_session.query(Candle).filter(
            Candle.instrument_key == instrument_key,
            Candle.interval == "1minute"
        ).order_by(desc(Candle.timestamp)).first()
        
        if latest_candle:
            print(f"📈 Latest candle: {latest_candle.timestamp} - Close: {latest_candle.close}")
        else:
            print(f"❌ No candles found in database")
            
        # Check if stock is in watchlist
        from app.models import WatchlistStock
        watchlist_entry = db_session.query(WatchlistStock).filter(
            WatchlistStock.instrument_key == instrument_key
        ).first()
        
        if watchlist_entry:
            print(f"📋 Stock is in watchlist: {watchlist_entry.symbol}")
        else:
            print(f"❌ Stock is NOT in watchlist")
            print(f"💡 This might explain why data isn't being fetched")
            
    except Exception as e:
        print(f"❌ Database error: {e}")
    finally:
        db_session.close()

def test_chart_endpoint():
    """Test the actual chart endpoint."""
    print(f"\n🌐 Testing Chart Endpoint")
    print("=" * 30)
    
    import requests
    
    instrument_key = "NSE_EQ|INE335Y01020"
    
    try:
        # Test the chart page
        url = f"http://localhost:8000/chart/{instrument_key}"
        print(f"📡 Testing chart page: {url}")
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print(f"   ✅ Chart page loads successfully")
            
            if "Stock not found" in response.text:
                print(f"   ❌ Stock not found error")
            else:
                print(f"   ✅ Chart page content looks good")
        else:
            print(f"   ❌ Chart page failed: {response.status_code}")
            
        # Test the chart data endpoint
        data_url = f"http://localhost:8000/chart_data/{instrument_key}?interval=1minute"
        print(f"📡 Testing chart data: {data_url}")
        
        response = requests.get(data_url, timeout=30)
        
        if response.status_code == 200:
            print(f"   ✅ Chart data endpoint works")
            print(f"   📊 Response length: {len(response.text)} characters")
            
            if "Could not find" in response.text:
                print(f"   ❌ No data found error")
            elif "plotly" in response.text.lower():
                print(f"   ✅ Contains Plotly chart")
            else:
                print(f"   ⚠️ Response unclear")
        else:
            print(f"   ❌ Chart data failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Endpoint test error: {e}")

def main():
    """Run all tests for the specific instrument."""
    print("🔍 SPECIFIC INSTRUMENT DIAGNOSTICS")
    print("Investigating: NSE_EQ|INE335Y01020 intraday data issues")
    print("=" * 80)
    
    test_specific_instrument()
    test_database_data()
    test_chart_endpoint()
    
    print("\n" + "=" * 80)
    print("📋 DIAGNOSTIC SUMMARY:")
    print("Check the results above to identify the specific issue:")
    print("1. ✅ Stock in database - Is the stock properly registered?")
    print("2. ✅ Data fetching - Is data being retrieved from API?")
    print("3. ✅ Chart generation - Are charts being created?")
    print("4. ✅ Endpoint access - Is the web interface working?")
    
    print("\n💡 Common Issues:")
    print("- Stock not in watchlist: Data won't be fetched automatically")
    print("- Stock not in database: Charts can't be generated")
    print("- Wrong instrument key: API calls will fail")
    print("- Box size issues: Charts may appear empty")

if __name__ == "__main__":
    main()
