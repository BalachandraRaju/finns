#!/usr/bin/env python3
"""
Test script to verify IRCTC intraday data flow from API to chart display.
"""

import sys
import os
import datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import charts
from app.db import SessionLocal
from app.models import Candle
from sqlalchemy import func, desc, and_

def test_irctc_data_flow():
    """Test the complete data flow for IRCTC."""
    print("🔍 Testing IRCTC Data Flow: API → Database → Chart")
    print("=" * 60)
    
    instrument_key = "NSE_EQ|INE335Y01020"  # IRCTC
    today = datetime.date.today()
    
    print(f"📅 Testing for date: {today}")
    print(f"📊 Instrument: {instrument_key} (IRCTC)")
    
    # Step 1: Check what's in the database
    print(f"\n1️⃣ DATABASE CHECK:")
    db_session = SessionLocal()
    
    try:
        # Check today's 1-minute candles
        today_candles = db_session.query(Candle).filter(
            and_(
                Candle.instrument_key == instrument_key,
                Candle.interval == "1minute",
                func.date(Candle.timestamp) == today
            )
        ).order_by(Candle.timestamp).all()
        
        print(f"   📊 Today's 1-minute candles in DB: {len(today_candles)}")
        
        if today_candles:
            earliest = today_candles[0]
            latest = today_candles[-1]
            print(f"   📈 Earliest today: {earliest.timestamp} - Close: {earliest.close}")
            print(f"   📉 Latest today: {latest.timestamp} - Close: {latest.close}")
            
            # Check time distribution
            morning_candles = [c for c in today_candles if c.timestamp.hour < 12]
            afternoon_candles = [c for c in today_candles if c.timestamp.hour >= 12]
            
            print(f"   🌅 Morning candles (before 12 PM): {len(morning_candles)}")
            print(f"   🌇 Afternoon candles (after 12 PM): {len(afternoon_candles)}")
            
            # Show sample of recent candles
            print(f"   📋 Last 5 candles:")
            for candle in today_candles[-5:]:
                print(f"      {candle.timestamp} | O:{candle.open} H:{candle.high} L:{candle.low} C:{candle.close}")
        else:
            print(f"   ❌ No today's candles found in database")
            
    except Exception as e:
        print(f"   ❌ Database error: {e}")
    finally:
        db_session.close()
    
    # Step 2: Test data retrieval function
    print(f"\n2️⃣ DATA RETRIEVAL TEST:")
    try:
        start_date = today
        end_date = today
        
        print(f"   📡 Calling get_candles_for_instrument({instrument_key}, '1minute', {start_date}, {end_date})")
        
        candles = charts.get_candles_for_instrument(instrument_key, "1minute", start_date, end_date)
        
        print(f"   📊 Retrieved {len(candles)} candles")
        
        if candles:
            print(f"   📈 First candle: {candles[0]['timestamp']} - Close: {candles[0]['close']}")
            print(f"   📉 Last candle: {candles[-1]['timestamp']} - Close: {candles[-1]['close']}")
            
            # Check if we have current time data
            current_hour = datetime.datetime.now().hour
            recent_candles = [c for c in candles if current_hour - 2 <= datetime.datetime.strptime(c['timestamp'], '%Y-%m-%d %H:%M:%S').hour <= current_hour]
            
            print(f"   🕐 Recent candles (last 2 hours): {len(recent_candles)}")
            
            if recent_candles:
                print(f"   📋 Recent candles sample:")
                for candle in recent_candles[-3:]:
                    print(f"      {candle['timestamp']} | Close: {candle['close']}")
        else:
            print(f"   ❌ No candles retrieved by function")
            
    except Exception as e:
        print(f"   ❌ Retrieval error: {e}")
    
    # Step 3: Test P&F calculation
    print(f"\n3️⃣ P&F CALCULATION TEST:")
    try:
        if candles:
            highs = [float(c['high']) for c in candles]
            lows = [float(c['low']) for c in candles]
            
            print(f"   📊 Price data: {len(highs)} points")
            print(f"   📈 Price range: {min(lows):.2f} to {max(highs):.2f}")
            
            # Test with appropriate box size for IRCTC (around 785)
            box_pct = 0.0025  # 0.25%
            
            x_coords, y_coords, pnf_symbols = charts._calculate_pnf_points(highs, lows, box_pct, 3)
            
            print(f"   📊 P&F points generated: {len(x_coords)}")
            
            if x_coords:
                x_count = sum(1 for s in pnf_symbols if s == 'X')
                o_count = sum(1 for s in pnf_symbols if s == 'O')
                columns = max(x_coords)
                
                print(f"   ✅ X's: {x_count}, O's: {o_count}, Columns: {columns}")
                print(f"   📈 P&F price range: {min(y_coords):.2f} to {max(y_coords):.2f}")
                
                # Show first few P&F points
                print(f"   📋 First 5 P&F points:")
                for i in range(min(5, len(x_coords))):
                    print(f"      {i+1}. Column {x_coords[i]}: {pnf_symbols[i]} at {y_coords[i]:.2f}")
            else:
                print(f"   ❌ No P&F points generated")
        else:
            print(f"   ⏭️ Skipping P&F test - no candle data")
            
    except Exception as e:
        print(f"   ❌ P&F calculation error: {e}")
    
    # Step 4: Test chart generation
    print(f"\n4️⃣ CHART GENERATION TEST:")
    try:
        chart_html = charts.generate_pnf_chart_html(
            instrument_key, 
            box_pct=0.0025, 
            interval="1minute", 
            time_range="1month"
        )
        
        if chart_html:
            print(f"   ✅ Chart HTML generated: {len(chart_html)} characters")
            
            # Check for actual data in the chart
            if "Could not find" in chart_html:
                print(f"   ❌ Chart shows 'Could not find' error")
            elif '"x":[]' in chart_html or '"y":[]' in chart_html:
                print(f"   ❌ Chart has empty data arrays")
            elif '"x":[' in chart_html and '"y":[' in chart_html:
                print(f"   ✅ Chart contains data arrays")
                
                # Extract a sample of the data
                import re
                x_match = re.search(r'"x":\[([^\]]+)\]', chart_html)
                y_match = re.search(r'"y":\[([^\]]+)\]', chart_html)
                
                if x_match and y_match:
                    x_data = x_match.group(1).split(',')[:5]  # First 5 points
                    y_data = y_match.group(1).split(',')[:5]  # First 5 points
                    print(f"   📊 Sample chart data:")
                    for i in range(len(x_data)):
                        print(f"      Point {i+1}: x={x_data[i].strip()}, y={y_data[i].strip()}")
            else:
                print(f"   ⚠️ Chart data format unclear")
        else:
            print(f"   ❌ No chart HTML generated")
            
    except Exception as e:
        print(f"   ❌ Chart generation error: {e}")

def test_live_api_vs_database():
    """Compare live API data with database data."""
    print(f"\n🔄 LIVE API vs DATABASE COMPARISON:")
    print("=" * 50)
    
    instrument_key = "NSE_EQ|INE335Y01020"
    
    # Get live API data
    print(f"📡 Fetching live API data...")
    try:
        from app.upstox_client import get_current_intraday_data
        
        live_data = get_current_intraday_data(instrument_key, "1minute")
        
        if live_data:
            print(f"   ✅ Live API returned {len(live_data)} candles")
            if live_data:
                latest_live = live_data[-1]
                print(f"   📈 Latest live: {latest_live['datetime']} - Close: {latest_live['close']}")
        else:
            print(f"   ❌ No live data from API")
            
    except Exception as e:
        print(f"   ❌ Live API error: {e}")
    
    # Get database data
    print(f"💾 Checking database data...")
    try:
        today = datetime.date.today()
        candles = charts.get_candles_for_instrument(instrument_key, "1minute", today, today)
        
        if candles:
            print(f"   ✅ Database returned {len(candles)} candles")
            latest_db = candles[-1]
            print(f"   📈 Latest DB: {latest_db['timestamp']} - Close: {latest_db['close']}")
            
            # Compare timestamps
            if live_data and candles:
                live_time = latest_live['datetime']
                db_time = latest_db['timestamp']
                print(f"   🕐 Time comparison:")
                print(f"      Live API: {live_time}")
                print(f"      Database: {db_time}")
                
                if live_time == db_time:
                    print(f"      ✅ Times match - data is in sync")
                else:
                    print(f"      ⚠️ Times differ - possible sync issue")
        else:
            print(f"   ❌ No database data")
            
    except Exception as e:
        print(f"   ❌ Database comparison error: {e}")

def main():
    """Run complete IRCTC data flow test."""
    print("🔍 IRCTC INTRADAY DATA FLOW VERIFICATION")
    print("Checking: API → Database → Chart pipeline")
    print("=" * 80)
    
    test_irctc_data_flow()
    test_live_api_vs_database()
    
    print("\n" + "=" * 80)
    print("📋 DATA FLOW ANALYSIS:")
    print("1. ✅ Database Check - Are today's candles stored?")
    print("2. ✅ Retrieval Test - Does get_candles_for_instrument work?")
    print("3. ✅ P&F Calculation - Are P&F points generated?")
    print("4. ✅ Chart Generation - Does the chart contain data?")
    print("5. ✅ API vs DB - Is data in sync?")
    
    print("\n💡 If charts still don't show:")
    print("- Check browser cache (hard refresh)")
    print("- Verify box size is appropriate (0.25% for IRCTC)")
    print("- Check if data is actually reaching the frontend")
    print("- Look for JavaScript errors in browser console")

if __name__ == "__main__":
    main()
