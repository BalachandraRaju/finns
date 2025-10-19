#!/usr/bin/env python3
"""
Test script to verify the new intraday mode with historical context.
"""

import sys
import os
import datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import charts

def test_intraday_mode_with_context():
    """Test intraday mode includes historical data for analysis."""
    print("🚨 Testing Intraday Mode with Historical Context")
    print("=" * 60)
    
    instrument_key = "NSE_EQ|INE335Y01020"  # IRCTC
    today = datetime.date.today()
    
    print(f"📅 Testing for: {instrument_key} (IRCTC)")
    print(f"🕐 Today: {today}")
    
    # Test the intraday data fetching function
    print(f"\n1️⃣ Testing get_intraday_candles_with_fallback:")
    try:
        intraday_candles = charts.get_intraday_candles_with_fallback(instrument_key, "1minute")
        
        print(f"   📊 Total candles retrieved: {len(intraday_candles)}")
        
        if intraday_candles:
            # Analyze the data range
            earliest = intraday_candles[0]
            latest = intraday_candles[-1]
            
            earliest_date = datetime.datetime.strptime(earliest['timestamp'], '%Y-%m-%d %H:%M:%S').date()
            latest_date = datetime.datetime.strptime(latest['timestamp'], '%Y-%m-%d %H:%M:%S').date()
            
            print(f"   📈 Data range: {earliest_date} to {latest_date}")
            print(f"   📉 Earliest: {earliest['timestamp']} - Close: {earliest['close']}")
            print(f"   📈 Latest: {latest['timestamp']} - Close: {latest['close']}")
            
            # Count candles by date
            date_counts = {}
            today_candles = []
            
            for candle in intraday_candles:
                candle_date = datetime.datetime.strptime(candle['timestamp'], '%Y-%m-%d %H:%M:%S').date()
                date_counts[candle_date] = date_counts.get(candle_date, 0) + 1
                
                if candle_date == today:
                    today_candles.append(candle)
            
            print(f"\n   📊 Candles by date:")
            for date, count in sorted(date_counts.items()):
                is_today = "👈 TODAY" if date == today else ""
                print(f"      {date}: {count} candles {is_today}")
            
            print(f"\n   🚨 Today's live candles: {len(today_candles)}")
            if today_candles:
                print(f"      Latest today: {today_candles[-1]['timestamp']} - Close: {today_candles[-1]['close']}")
            
            # Check if we have sufficient historical context
            historical_days = len([d for d in date_counts.keys() if d < today])
            print(f"   📅 Historical trading days: {historical_days}")
            
            if historical_days >= 3:
                print(f"   ✅ Good historical context for analysis")
            else:
                print(f"   ⚠️ Limited historical context")
                
        else:
            print(f"   ❌ No candles retrieved")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test chart generation in intraday mode
    print(f"\n2️⃣ Testing intraday chart generation:")
    try:
        chart_html = charts.generate_pnf_chart_html(
            instrument_key, 
            box_pct=0.0025, 
            interval="1minute", 
            time_range="today",
            mode="intraday"
        )
        
        if chart_html:
            print(f"   ✅ Chart generated: {len(chart_html)} characters")
            
            # Check for intraday indicators in title
            if "LIVE INTRADAY" in chart_html:
                print(f"   ✅ Chart shows intraday mode in title")
            else:
                print(f"   ⚠️ Chart may not show intraday mode")
            
            # Check for data
            if '"x":[]' in chart_html or '"y":[]' in chart_html:
                print(f"   ❌ Chart has empty data arrays")
            elif '"x":[' in chart_html and '"y":[' in chart_html:
                print(f"   ✅ Chart contains plot data")
                
                # Extract sample data to verify it includes historical context
                import re
                x_match = re.search(r'"x":\[([^\]]+)\]', chart_html)
                if x_match:
                    x_data = x_match.group(1).split(',')
                    max_column = max([int(x.strip()) for x in x_data if x.strip().isdigit()])
                    print(f"   📊 Chart has {max_column} columns (good for analysis)")
            else:
                print(f"   ⚠️ Chart data format unclear")
        else:
            print(f"   ❌ No chart generated")
            
    except Exception as e:
        print(f"   ❌ Chart generation error: {e}")

def test_intraday_vs_regular_1minute():
    """Compare intraday mode vs regular 1-minute mode."""
    print(f"\n🔄 Comparing Intraday Mode vs Regular 1-Minute")
    print("=" * 60)
    
    instrument_key = "NSE_EQ|INE335Y01020"
    
    # Test regular 1-minute mode (1 month)
    print(f"📊 Regular 1-minute mode (1 month):")
    try:
        regular_candles = charts.get_candles_for_instrument(
            instrument_key, "1minute", 
            datetime.date.today() - datetime.timedelta(days=30), 
            datetime.date.today()
        )
        print(f"   📈 Regular mode: {len(regular_candles)} candles")
    except Exception as e:
        print(f"   ❌ Regular mode error: {e}")
        regular_candles = []
    
    # Test intraday mode
    print(f"🚨 Intraday mode (last 7 days + live):")
    try:
        intraday_candles = charts.get_intraday_candles_with_fallback(instrument_key, "1minute")
        print(f"   📈 Intraday mode: {len(intraday_candles)} candles")
    except Exception as e:
        print(f"   ❌ Intraday mode error: {e}")
        intraday_candles = []
    
    # Compare data ranges
    if regular_candles and intraday_candles:
        today = datetime.date.today()
        
        # Count today's candles in each mode
        regular_today = [c for c in regular_candles if str(today) in str(c['timestamp'])]
        intraday_today = [c for c in intraday_candles if str(today) in str(c['timestamp'])]
        
        print(f"\n📊 Comparison:")
        print(f"   Regular mode today's candles: {len(regular_today)}")
        print(f"   Intraday mode today's candles: {len(intraday_today)}")
        
        if len(intraday_today) >= len(regular_today):
            print(f"   ✅ Intraday mode has same or more current data")
        else:
            print(f"   ⚠️ Intraday mode has less current data")
        
        # Check if intraday mode has good historical context
        intraday_historical = len(intraday_candles) - len(intraday_today)
        print(f"   Intraday historical candles: {intraday_historical}")
        
        if intraday_historical > 500:  # At least a few days of 1-minute data
            print(f"   ✅ Good historical context for analysis")
        else:
            print(f"   ⚠️ Limited historical context")

def main():
    """Run all intraday mode tests."""
    print("🚨 INTRADAY MODE WITH HISTORICAL CONTEXT TESTING")
    print("Testing: Last 7 days + today's live data for proper analysis")
    print("=" * 80)
    
    test_intraday_mode_with_context()
    test_intraday_vs_regular_1minute()
    
    print("\n" + "=" * 80)
    print("📋 INTRADAY MODE TEST SUMMARY:")
    print("✅ Historical Context - Does intraday include previous days?")
    print("✅ Live Data - Does intraday include today's current data?")
    print("✅ Chart Generation - Does intraday mode create proper charts?")
    print("✅ Data Comparison - How does intraday compare to regular mode?")
    
    print("\n💡 Expected Results:")
    print("- Intraday mode should include 7-10 days of historical data")
    print("- Plus today's live data (auto-fetched if missing)")
    print("- Chart title should show 'LIVE INTRADAY'")
    print("- Sufficient data for meaningful P&F analysis")
    print("- Better than regular 1-minute for live trading analysis")

if __name__ == "__main__":
    main()
