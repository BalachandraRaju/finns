#!/usr/bin/env python3
"""
Test script to verify intraday chart functionality.
"""

import sys
import datetime
sys.path.append('.')

from app import charts

def test_intraday_data_fetching():
    """Test fetching different intervals of data"""
    
    print("Testing Intraday Chart Data Fetching...")
    print("=" * 50)
    
    # TCS instrument key
    instrument_key = "NSE_EQ|INE467B01029"
    
    intervals_to_test = [
        ("day", "Daily Data"),
        ("30minute", "30-Minute Data"),
        ("3minute", "3-Minute Data"),
        ("1minute", "1-Minute Data")
    ]
    
    for interval, description in intervals_to_test:
        print(f"\n📊 Testing {description} ({interval}):")
        print("-" * 30)
        
        try:
            # Get data for the last few days
            today = datetime.date.today()
            if interval == "day":
                start_date = today - datetime.timedelta(days=30)
            elif interval == "30minute":
                start_date = today - datetime.timedelta(days=7)
            else:  # 1minute, 3minute
                start_date = today - datetime.timedelta(days=3)
            
            candles = charts.get_candles_for_instrument(instrument_key, interval, start_date, today)
            
            if candles:
                print(f"✅ Successfully fetched {len(candles)} candles")
                if len(candles) >= 3:
                    print(f"   Latest 3 candles:")
                    for i, candle in enumerate(candles[-3:]):
                        timestamp = candle['timestamp']
                        close = candle['close']
                        print(f"   {i+1}. {timestamp} - Close: {close}")
                else:
                    print(f"   Sample candle: {candles[-1]}")
            else:
                print(f"❌ No data available for {interval}")
                
        except Exception as e:
            print(f"❌ Error fetching {interval} data: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Intraday data testing completed!")
    print("\nNow you can:")
    print("1. Open http://127.0.0.1:8000/chart/NSE_EQ%7CINE467B01029")
    print("2. Select different intervals from the dropdown")
    print("3. See intraday P&F charts with 1-minute, 3-minute, or 30-minute data")

if __name__ == "__main__":
    test_intraday_data_fetching()
