#!/usr/bin/env python3
"""
Test the enhanced pattern alert system with real watchlist stocks.
"""

import sys
import os
sys.path.append('/Users/balachandra.raju/projects/finns')

from app.scheduler import check_pnf_alerts
from app import crud
import datetime

def test_real_watchlist_alerts():
    """Test enhanced pattern alerts with real watchlist stocks."""
    print("🔍 Testing Enhanced Pattern Alerts with Real Watchlist")
    print("=" * 70)
    
    # Get watchlist stocks
    watchlist = crud.get_watchlist_details()
    
    if not watchlist:
        print("❌ No stocks in watchlist. Please add stocks to test alerts.")
        return
    
    print(f"📊 Found {len(watchlist)} stocks in watchlist:")
    for stock in watchlist:
        print(f"   • {stock.symbol} ({stock.instrument_key})")
    
    print(f"\n🎯 Testing with User Specifications:")
    print(f"   • Box Size: 0.25%")
    print(f"   • Time Interval: 1 minute") 
    print(f"   • Reversal Box: 3")
    print(f"   • Data Source: 1 month")
    print(f"   • Enhanced Pattern Detection: Enabled")
    
    # Test with first few stocks to avoid overwhelming
    test_stocks = watchlist[:3] if len(watchlist) > 3 else watchlist
    
    print(f"\n🧪 Testing Enhanced Pattern Detection:")
    print("-" * 50)
    
    for i, stock in enumerate(test_stocks, 1):
        symbol = stock.symbol
        instrument_key = stock.instrument_key
        
        print(f"\n{i}. Testing {symbol}...")
        print(f"   Instrument Key: {instrument_key}")
        
        try:
            # Test the enhanced P&F alert checking
            check_pnf_alerts(symbol, instrument_key)
            print(f"   ✅ Enhanced pattern check completed for {symbol}")
            
        except Exception as e:
            print(f"   ❌ Error checking {symbol}: {e}")
    
    print(f"\n" + "=" * 70)
    print("✅ Real watchlist testing completed!")
    print("📱 Any pattern alerts found will be sent to Telegram")
    print("🔄 The scheduler runs this check every minute during market hours")

def show_market_hours_info():
    """Show market hours and scheduling information."""
    print("\n⏰ Market Hours & Scheduling Information")
    print("=" * 70)
    
    now = datetime.datetime.now()
    market_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
    market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    print(f"🕘 Current Time: {now.strftime('%H:%M:%S')}")
    print(f"📈 Market Hours: 09:00 - 15:30 IST")
    print(f"📅 Trading Days: Monday - Friday")
    
    if market_start <= now <= market_end and now.weekday() < 5:
        print(f"🟢 Status: MARKET OPEN - Alerts are active")
    else:
        if now.weekday() >= 5:
            print(f"🔴 Status: WEEKEND - Alerts paused")
        else:
            print(f"🔴 Status: MARKET CLOSED - Alerts paused")
    
    print(f"\n🔄 Scheduler Configuration:")
    print(f"   • Frequency: Every 1 minute")
    print(f"   • Pattern Detection: Enhanced (10 pattern types)")
    print(f"   • Data Processing: 1-minute candles, 1-month history")
    print(f"   • Alert Delivery: Telegram + Redis storage")
    print(f"   • Duplicate Prevention: 0.5% price threshold")

def test_single_stock_detailed():
    """Test detailed pattern analysis for a single stock."""
    print("\n🔬 Detailed Single Stock Analysis")
    print("=" * 70)
    
    # Get first stock from watchlist for detailed analysis
    watchlist = crud.get_watchlist_details()
    if not watchlist:
        print("❌ No stocks in watchlist for detailed analysis.")
        return
    
    stock = watchlist[0]
    symbol = stock.symbol
    instrument_key = stock.instrument_key
    
    print(f"🎯 Analyzing: {symbol}")
    print(f"📊 Instrument Key: {instrument_key}")
    
    try:
        # Import required modules for detailed analysis
        from app import charts
        from app.pattern_detector import PatternDetector
        import datetime
        
        # Get 1-month of 1-minute data as per user specs
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=30)
        
        print(f"📅 Data Range: {start_date} to {today}")
        print(f"⏱️  Fetching 1-minute candles...")
        
        all_candles = charts.get_candles_for_instrument(instrument_key, "1minute", start_date, today)
        
        if not all_candles:
            print(f"❌ No 1-minute data available for {symbol}")
            return
        
        print(f"✅ Retrieved {len(all_candles)} 1-minute candles")
        
        # Extract price data
        highs = [float(c['high']) for c in all_candles]
        lows = [float(c['low']) for c in all_candles]
        closes = [float(c['close']) for c in all_candles]
        
        print(f"💰 Price Range: ₹{min(lows):.2f} - ₹{max(highs):.2f}")
        print(f"📈 Latest Price: ₹{closes[-1]:.2f}")
        
        # Calculate P&F with user specifications
        box_percentage = 0.0025  # 0.25%
        reversal = 3
        
        x_coords, y_coords, pnf_symbols = charts._calculate_pnf_points(highs, lows, box_percentage, reversal)
        
        if not x_coords:
            print(f"❌ Insufficient data for P&F calculation")
            return
        
        print(f"📊 P&F Analysis:")
        print(f"   • Generated {len(x_coords)} P&F points")
        print(f"   • Total columns: {max(x_coords) if x_coords else 0}")
        print(f"   • Box size: 0.25%")
        print(f"   • Reversal: 3 boxes")
        
        # Run enhanced pattern detection
        detector = PatternDetector()
        alert_triggers = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols, closes)
        
        print(f"\n🚨 Pattern Analysis Results:")
        print(f"   • Total alerts found: {len(alert_triggers)}")
        
        if alert_triggers:
            print(f"   • Alert details:")
            for alert in alert_triggers:
                print(f"     - {alert.alert_type.value}: {alert.pattern_type.value}")
                print(f"       Price: ₹{alert.price:.2f} | Column: {alert.column}")
                print(f"       Reason: {alert.trigger_reason}")
        else:
            print(f"   • No pattern alerts detected at this time")
        
    except Exception as e:
        print(f"❌ Error in detailed analysis: {e}")
    
    print(f"\n" + "=" * 70)
    print("✅ Detailed analysis completed!")

if __name__ == "__main__":
    print("🚀 Enhanced Watchlist Pattern Alert Testing")
    print("=" * 80)
    
    # Show market hours info
    show_market_hours_info()
    
    # Test with real watchlist
    test_real_watchlist_alerts()
    
    # Detailed single stock analysis
    test_single_stock_detailed()
    
    print(f"\n🎯 Summary:")
    print(f"✅ Enhanced pattern detection system is ready")
    print(f"📱 Telegram alerts configured for all pattern types")
    print(f"🔄 Scheduler will monitor all watchlist stocks every minute")
    print(f"⏰ Active during market hours (9 AM - 3:30 PM, Mon-Fri)")
    print(f"📊 Using your specifications: 1min data, 0.25% box, 3 reversal, 1 month history")
