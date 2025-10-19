#!/usr/bin/env python3
"""
Test script to verify RSI alert functionality.
"""

import os
import sys
import datetime
sys.path.append('.')

from app import alerts, charts, crud
from dotenv import load_dotenv

load_dotenv()

def test_rsi_calculation():
    """Test RSI calculation with sample data"""
    
    print("Testing RSI calculation...")
    
    # Sample closing prices (trending up to test overbought)
    sample_prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 111, 110, 112, 114, 113, 115, 117]
    
    # Test RSI calculation
    rsi_9 = alerts.calculate_rsi(sample_prices, period=9)
    rsi_14 = alerts.calculate_rsi(sample_prices, period=14)
    
    print(f"Sample prices: {sample_prices[-10:]}")  # Show last 10 prices
    print(f"RSI (9-period): {rsi_9:.2f}" if rsi_9 else "RSI (9-period): Not enough data")
    print(f"RSI (14-period): {rsi_14:.2f}" if rsi_14 else "RSI (14-period): Not enough data")
    
    return rsi_9


def test_rsi_alerts_with_real_data():
    """Test RSI alerts with real market data"""
    
    print("\nTesting RSI alerts with real data...")
    
    # TCS instrument key
    instrument_key = "NSE_EQ|INE467B01029"
    symbol = "TCS"
    
    try:
        # Get 3-minute data for the last 3 days
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=3)
        
        print(f"Fetching 3-minute data (aggregated from 1-minute) for {symbol} from {start_date} to {today}")
        # Fetch 1-minute data and aggregate to 3-minute
        candle_data_1min = charts.get_candles_for_instrument(instrument_key, "1minute", start_date, today)
        candle_data = charts.aggregate_to_3minute(candle_data_1min)
        
        if not candle_data:
            print("❌ No 3-minute data available")
            return
        
        print(f"✅ Retrieved {len(candle_data)} 3-minute candles (aggregated from 1-minute data)")
        
        # Show last few closing prices
        if len(candle_data) >= 5:
            recent_closes = [float(c['close']) for c in candle_data[-5:]]
            print(f"Recent closing prices: {recent_closes}")
        
        # Calculate current RSI
        closes = [float(c['close']) for c in candle_data]
        current_rsi = alerts.calculate_rsi(closes, period=9)
        
        if current_rsi:
            print(f"Current RSI (9-period): {current_rsi:.2f}")
            
            # Test overbought alert
            overbought_alert = alerts.find_rsi_overbought_alert(candle_data, symbol, rsi_threshold=60, period=9)
            if overbought_alert:
                print(f"🔴 OVERBOUGHT ALERT: {overbought_alert}")
            else:
                print(f"✅ No overbought alert (RSI: {current_rsi:.2f} <= 60)")
            
            # Test oversold alert
            oversold_alert = alerts.find_rsi_oversold_alert(candle_data, symbol, rsi_threshold=40, period=9)
            if oversold_alert:
                print(f"🟢 OVERSOLD ALERT: {oversold_alert}")
            else:
                print(f"✅ No oversold alert (RSI: {current_rsi:.2f} >= 40)")
        else:
            print("❌ Could not calculate RSI - insufficient data")
            
    except Exception as e:
        print(f"❌ Error testing RSI alerts: {e}")


def test_scheduler_rsi_function():
    """Test the scheduler's RSI alert function"""
    
    print("\nTesting scheduler RSI function...")
    
    # Import the scheduler function
    from app.scheduler import check_rsi_alerts
    
    # Test with TCS
    symbol = "TCS"
    instrument_key = "NSE_EQ|INE467B01029"
    
    try:
        check_rsi_alerts(symbol, instrument_key)
        print("✅ Scheduler RSI function executed successfully")
    except Exception as e:
        print(f"❌ Error in scheduler RSI function: {e}")


if __name__ == "__main__":
    print("🔍 RSI Alert System Test")
    print("=" * 40)
    
    # Test 1: RSI calculation
    rsi_value = test_rsi_calculation()
    
    # Test 2: Real data alerts
    test_rsi_alerts_with_real_data()
    
    # Test 3: Scheduler function
    test_scheduler_rsi_function()
    
    print("\n" + "=" * 40)
    print("✅ RSI alert testing completed!")
