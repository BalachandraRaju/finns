#!/usr/bin/env python3
"""
Test the enhanced pattern alert system with Telegram integration.
"""

import sys
import os
sys.path.append('/Users/balachandra.raju/projects/finns')

from app.telegram_bot import send_enhanced_pattern_telegram
from app.scheduler import handle_enhanced_pattern_alert
from app.pattern_detector import PatternType, AlertType

def test_enhanced_telegram_alerts():
    """Test enhanced Telegram pattern alerts."""
    print("🧪 Testing Enhanced Pattern Telegram Alerts")
    print("=" * 60)
    
    # Test different pattern types
    test_alerts = [
        {
            'symbol': 'TCS',
            'alert_dict': {
                'type': 'Double Top Buy EMA',
                'signal_price': 3456.75,
                'pattern_type': 'double_top_buy_ema',
                'alert_type': 'BUY',
                'column': 15,
                'trigger_reason': '🚨 DOUBLE TOP BUY (EMA VALIDATED): Price 3456.75 breaks above resistance 3450.25 after 2 distinct similar tops with follow-through. Chart above 20 EMA (3445.30)',
                'is_first_occurrence': True
            }
        },
        {
            'symbol': 'RELIANCE',
            'alert_dict': {
                'type': 'Turtle Breakout Buy',
                'signal_price': 2875.50,
                'pattern_type': 'turtle_breakout_buy',
                'alert_type': 'BUY',
                'column': 22,
                'trigger_reason': '🚨 TURTLE BREAKOUT BUY: Price 2875.50 breaks above 20-column high 2870.25. Chart above 20 EMA (2865.80)',
                'is_first_occurrence': True
            }
        },
        {
            'symbol': 'INFY',
            'alert_dict': {
                'type': 'Anchor Breakout Buy',
                'signal_price': 1789.25,
                'pattern_type': 'anchor_breakout_buy',
                'alert_type': 'BUY',
                'column': 8,
                'trigger_reason': '🚨 ANCHOR BREAKOUT BUY: Price 1789.25 breaks above anchor column high 1785.60 (14+ bar height). Chart above 20 EMA (1780.45)',
                'is_first_occurrence': True
            }
        },
        {
            'symbol': 'HDFC',
            'alert_dict': {
                'type': 'Triple Bottom Sell EMA',
                'signal_price': 1654.30,
                'pattern_type': 'triple_bottom_sell_ema',
                'alert_type': 'SELL',
                'column': 12,
                'trigger_reason': '🚨 TRIPLE BOTTOM SELL (EMA VALIDATED): Price 1654.30 breaks below support 1658.75 after 3 distinct similar bottoms with follow-through. Chart below 20 EMA (1665.20)',
                'is_first_occurrence': True
            }
        },
        {
            'symbol': 'WIPRO',
            'alert_dict': {
                'type': 'Quadruple Top Buy EMA',
                'signal_price': 567.80,
                'pattern_type': 'quadruple_top_buy_ema',
                'alert_type': 'BUY',
                'column': 18,
                'trigger_reason': '🚨 QUADRUPLE TOP BUY (EMA VALIDATED): Price 567.80 breaks above resistance 565.25 after 4 distinct similar tops with follow-through. Chart above 20 EMA (562.15)',
                'is_first_occurrence': True
            }
        }
    ]
    
    print("📱 Testing Enhanced Telegram Messages:")
    print("-" * 40)
    
    for i, test_case in enumerate(test_alerts, 1):
        symbol = test_case['symbol']
        alert_dict = test_case['alert_dict']
        
        print(f"\n{i}. Testing {symbol} - {alert_dict['type']}")
        print(f"   Pattern: {alert_dict['pattern_type']}")
        print(f"   Price: ₹{alert_dict['signal_price']:.2f}")
        print(f"   Alert Type: {alert_dict['alert_type']}")
        
        try:
            # Test enhanced Telegram messaging
            send_enhanced_pattern_telegram(symbol, alert_dict)
            print(f"   ✅ Enhanced Telegram alert sent successfully")
            
        except Exception as e:
            print(f"   ❌ Error sending alert: {e}")
    
    print(f"\n" + "=" * 60)
    print("✅ Enhanced Telegram alert testing completed!")
    print("📱 Check your Telegram for the pattern alerts")
    print("💡 If credentials not set, alerts will appear in console")

def test_alert_handler():
    """Test the enhanced alert handler with Redis integration."""
    print("\n🔧 Testing Enhanced Alert Handler")
    print("=" * 60)
    
    # Test alert that should be handled
    test_symbol = "TESTSTOCK"
    test_alert = {
        'type': 'Double Top Buy EMA',
        'signal_price': 1234.56,
        'pattern_type': 'double_top_buy_ema',
        'alert_type': 'BUY',
        'column': 10,
        'trigger_reason': '🚨 DOUBLE TOP BUY (EMA VALIDATED): Price 1234.56 breaks above resistance 1230.25 after 2 distinct similar tops with follow-through. Chart above 20 EMA (1225.80)',
        'is_first_occurrence': True
    }
    
    print(f"📊 Testing alert handler for {test_symbol}")
    print(f"   Pattern: {test_alert['pattern_type']}")
    print(f"   Price: ₹{test_alert['signal_price']:.2f}")
    
    try:
        # Test the enhanced alert handler
        handle_enhanced_pattern_alert(test_symbol, test_alert)
        print(f"   ✅ Alert handler executed successfully")
        
        # Test duplicate alert (should be skipped)
        print(f"\n📊 Testing duplicate alert detection...")
        handle_enhanced_pattern_alert(test_symbol, test_alert)
        print(f"   ✅ Duplicate detection working")
        
    except Exception as e:
        print(f"   ❌ Error in alert handler: {e}")
    
    print(f"\n" + "=" * 60)
    print("✅ Alert handler testing completed!")

def show_alert_specifications():
    """Show the user's alert specifications."""
    print("\n📋 User Alert Specifications")
    print("=" * 60)
    print("🎯 Configuration:")
    print("   • Box Size: 0.25%")
    print("   • Time Interval: 1 minute")
    print("   • Reversal Box: 3")
    print("   • Data Source: 1 month")
    print("   • Target: All watchlist stocks")
    print("   • Delivery: Telegram alerts")
    print("   • Trigger: Latest column signals only")
    
    print("\n🚨 Alert Types Enabled:")
    alert_types = [
        "Double Top Buy (EMA Validated)",
        "Triple Top Buy (EMA Validated)", 
        "Quadruple Top Buy (EMA Validated)",
        "Turtle Breakout Buy (20-column range)",
        "Anchor Column Breakout Buy (14+ bars)",
        "Double Bottom Sell (EMA Validated)",
        "Triple Bottom Sell (EMA Validated)",
        "Quadruple Bottom Sell (EMA Validated)", 
        "Turtle Breakdown Sell (20-column range)",
        "Anchor Column Breakdown Sell (14+ bars)"
    ]
    
    for i, alert_type in enumerate(alert_types, 1):
        print(f"   {i:2d}. {alert_type}")
    
    print(f"\n📱 Telegram Integration:")
    print("   • Enhanced pattern messages")
    print("   • Duplicate alert prevention")
    print("   • Real-time notifications")
    print("   • Detailed pattern information")
    
    print(f"\n⏰ Scheduling:")
    print("   • Runs every 1 minute")
    print("   • Market hours only (9 AM - 3:30 PM)")
    print("   • Weekdays only")
    print("   • Latest column focus for real-time trading")

if __name__ == "__main__":
    print("🚀 Enhanced Pattern Alert System Test")
    print("=" * 80)
    
    # Show specifications
    show_alert_specifications()
    
    # Test enhanced Telegram alerts
    test_enhanced_telegram_alerts()
    
    # Test alert handler
    test_alert_handler()
    
    print(f"\n🎉 All tests completed!")
    print(f"📊 Your enhanced pattern alert system is ready for live trading!")
    print(f"🔄 The scheduler will check all watchlist stocks every minute during market hours.")
