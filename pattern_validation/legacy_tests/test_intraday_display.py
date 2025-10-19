#!/usr/bin/env python3
"""
Test script to diagnose intraday chart display issues.
"""

import sys
import os
import datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import charts, crud

def test_1minute_data_availability():
    """Test if 1-minute data is available and being fetched correctly."""
    print("🔍 Testing 1-Minute Intraday Data Availability")
    print("=" * 60)
    
    # Test with TCS
    instrument_key = "NSE_EQ|INE467B01029"
    
    # Test different date ranges
    today = datetime.date.today()
    
    print(f"📅 Today: {today}")
    print(f"📊 Testing instrument: {instrument_key}")
    
    # Test 1: Today's data only
    print(f"\n1️⃣ Testing Today's Data Only:")
    try:
        candles_today = charts.get_candles_for_instrument(instrument_key, "1minute", today, today)
        print(f"   ✅ Found {len(candles_today)} 1-minute candles for today")
        
        if candles_today:
            latest = candles_today[-1]
            earliest = candles_today[0]
            print(f"   📈 Latest: {latest['timestamp']} - Close: {latest['close']}")
            print(f"   📉 Earliest: {earliest['timestamp']} - Close: {earliest['close']}")
        else:
            print(f"   ❌ No 1-minute data found for today")
            
    except Exception as e:
        print(f"   ❌ Error fetching today's data: {e}")
    
    # Test 2: Last 3 days
    print(f"\n2️⃣ Testing Last 3 Days:")
    start_date = today - datetime.timedelta(days=3)
    try:
        candles_3days = charts.get_candles_for_instrument(instrument_key, "1minute", start_date, today)
        print(f"   ✅ Found {len(candles_3days)} 1-minute candles for last 3 days")
        
        if candles_3days:
            latest = candles_3days[-1]
            earliest = candles_3days[0]
            print(f"   📈 Latest: {latest['timestamp']} - Close: {latest['close']}")
            print(f"   📉 Earliest: {earliest['timestamp']} - Close: {earliest['close']}")
            
            # Check if we have today's data
            today_candles = [c for c in candles_3days if c['timestamp'].startswith(str(today))]
            print(f"   🕐 Today's candles in dataset: {len(today_candles)}")
        else:
            print(f"   ❌ No 1-minute data found for last 3 days")
            
    except Exception as e:
        print(f"   ❌ Error fetching 3-day data: {e}")
    
    # Test 3: Chart generation
    print(f"\n3️⃣ Testing Chart Generation:")
    try:
        chart_html = charts.generate_pnf_chart_html(instrument_key, box_pct=0.01, interval="1minute", time_range="1month")
        
        if chart_html and "Could not find or fetch any chart data" not in chart_html:
            print(f"   ✅ Chart generated successfully")
            print(f"   📊 Chart HTML length: {len(chart_html)} characters")
            
            # Check if chart contains data
            if "data" in chart_html.lower() and "trace" in chart_html.lower():
                print(f"   📈 Chart appears to contain plot data")
            else:
                print(f"   ⚠️ Chart may not contain plot data")
        else:
            print(f"   ❌ Chart generation failed or no data")
            if chart_html:
                print(f"   Error message: {chart_html[:200]}...")
                
    except Exception as e:
        print(f"   ❌ Error generating chart: {e}")

def test_chart_endpoint():
    """Test the chart endpoint directly."""
    print(f"\n🌐 Testing Chart Endpoint")
    print("=" * 40)
    
    import requests
    
    # Test the chart endpoint
    instrument_key = "NSE_EQ|INE467B01029"
    
    try:
        # Test 1-minute chart endpoint
        url = f"http://localhost:8000/chart_data/{instrument_key}?interval=1minute&time_range=1month"
        print(f"📡 Testing URL: {url}")
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            print(f"   ✅ Endpoint responded successfully")
            print(f"   📊 Response length: {len(response.text)} characters")
            
            # Check if response contains chart data
            if "plotly" in response.text.lower():
                print(f"   📈 Response contains Plotly chart")
            else:
                print(f"   ⚠️ Response may not contain chart data")
                
            # Check for error messages
            if "could not find" in response.text.lower() or "missing data" in response.text.lower():
                print(f"   ❌ Chart shows data missing error")
            else:
                print(f"   ✅ No data missing errors detected")
                
        else:
            print(f"   ❌ Endpoint failed with status: {response.status_code}")
            print(f"   Error: {response.text[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Error testing endpoint: {e}")

def test_database_data():
    """Check what's actually in the database."""
    print(f"\n💾 Testing Database Data")
    print("=" * 30)
    
    from app.db import SessionLocal
    from app.models import Candle
    from sqlalchemy import func, desc
    
    db_session = SessionLocal()
    
    try:
        instrument_key = "NSE_EQ|INE467B01029"
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
            
        # Check date range
        date_range = db_session.query(
            func.min(Candle.timestamp),
            func.max(Candle.timestamp)
        ).filter(
            Candle.instrument_key == instrument_key,
            Candle.interval == "1minute"
        ).first()
        
        if date_range[0] and date_range[1]:
            print(f"📅 Data range: {date_range[0]} to {date_range[1]}")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
    finally:
        db_session.close()

def main():
    """Run all intraday display tests."""
    print("🔍 INTRADAY CHART DISPLAY DIAGNOSTICS")
    print("Investigating: Why intraday candles data is not displaying")
    print("=" * 80)
    
    test_1minute_data_availability()
    test_database_data()
    test_chart_endpoint()
    
    print("\n" + "=" * 80)
    print("📋 DIAGNOSTIC SUMMARY:")
    print("Check the results above to identify the issue:")
    print("1. ✅ Data availability - Are candles being fetched?")
    print("2. ✅ Database storage - Are candles being saved?")
    print("3. ✅ Chart generation - Is the chart being created?")
    print("4. ✅ Endpoint response - Is the web endpoint working?")
    
    print("\n💡 Common Issues:")
    print("- Market hours: Intraday data only available during trading hours")
    print("- Date range: Check if requesting correct date range")
    print("- API limits: Upstox may have rate limits")
    print("- Data processing: Check if aggregation is working")

if __name__ == "__main__":
    main()
