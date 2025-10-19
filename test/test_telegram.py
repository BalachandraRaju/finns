#!/usr/bin/env python3
"""
Test script for Telegram integration.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.telegram_notifier import test_telegram_connection, send_trading_alert
from datetime import datetime

def main():
    print("=" * 60)
    print("TELEGRAM INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Connection test
    print("\n1. Testing Telegram connection...")
    success = test_telegram_connection()
    if success:
        print("✅ Telegram connection test PASSED")
    else:
        print("❌ Telegram connection test FAILED")
        print("   Check your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env file")
        return
    
    # Test 2: Trading alert
    print("\n2. Testing trading alert...")
    success = send_trading_alert(
        symbol="TEST_STOCK",
        instrument_key="DHAN_99999",
        pattern_type="test_pattern",
        pattern_name="Test Pattern - Triple Top Buy",
        alert_type="BUY",
        signal_price=1234.56,
        matrix_score=8,
        is_super_alert=True,
        box_size=0.0025,
        interval="1minute",
        time_range="2months",
        trigger_reason="This is a test alert to verify Telegram integration is working correctly",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
    )
    
    if success:
        print("✅ Trading alert test PASSED")
        print("   Check your Telegram app for the alert message")
    else:
        print("❌ Trading alert test FAILED")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()

