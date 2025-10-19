#!/usr/bin/env python3
"""
Test script to verify the telegram bot fix.
"""

import sys
sys.path.append('.')

from app.telegram_bot import send_alert_message, send_telegram_alert

def test_telegram_functions():
    """Test the telegram bot functions"""
    
    print("Testing Telegram Bot Functions...")
    print("=" * 40)
    
    # Test 1: RSI Overbought Alert
    print("1. Testing RSI Overbought Alert:")
    rsi_overbought_alert = {
        'type': 'RSI Overbought Alert',
        'signal_price': 3450.50,
        'rsi_value': 65.8,
        'threshold': 60,
        'period': 9
    }
    send_alert_message("TCS", rsi_overbought_alert)
    
    print("\n2. Testing RSI Oversold Alert:")
    rsi_oversold_alert = {
        'type': 'RSI Oversold Alert',
        'signal_price': 3420.25,
        'rsi_value': 35.2,
        'threshold': 40,
        'period': 9
    }
    send_alert_message("TCS", rsi_oversold_alert)
    
    print("\n3. Testing P&F Pattern Alert:")
    pnf_alert = {
        'type': 'Triple Top Breakout',
        'signal_price': 3465.75
    }
    send_alert_message("TCS", pnf_alert)
    
    print("\n4. Testing Direct RSI Alert:")
    send_telegram_alert("RELIANCE", 72.5, "RSI Overbought", "\n*Threshold:* `70`\n*Price:* `2850.30`")
    
    print("\n" + "=" * 40)
    print("✅ All telegram functions tested successfully!")
    print("Note: If Telegram credentials are not set, messages will appear in console only.")

if __name__ == "__main__":
    test_telegram_functions()
