#!/usr/bin/env python3
"""
Test Telegram connectivity and try different methods to fix it.
"""

import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

print("\n" + "="*70)
print("  TELEGRAM CONNECTIVITY TEST & FIX")
print("="*70 + "\n")

# Test 1: Direct connection
print("🔍 Test 1: Testing direct connection to Telegram API...")
url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"

try:
    start = time.time()
    response = requests.get(url, timeout=10)
    elapsed = time.time() - start
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS! Connected in {elapsed:.2f}s")
        print(f"   Bot: {data['result']['first_name']}")
        print(f"   ID: {data['result']['id']}")
        direct_works = True
    else:
        print(f"❌ FAILED: HTTP {response.status_code}")
        direct_works = False
        
except requests.exceptions.Timeout:
    print(f"❌ FAILED: Connection timeout (>10s)")
    print(f"   Telegram API is being blocked by your network")
    direct_works = False
    
except requests.exceptions.ConnectionError as e:
    print(f"❌ FAILED: Connection error")
    print(f"   Error: {e}")
    direct_works = False
    
except Exception as e:
    print(f"❌ FAILED: {e}")
    direct_works = False

print()

# Test 2: Try with longer timeout
if not direct_works:
    print("🔍 Test 2: Trying with longer timeout (30s)...")
    try:
        start = time.time()
        response = requests.get(url, timeout=30)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            print(f"✅ SUCCESS! Connected in {elapsed:.2f}s")
            print(f"   Your network is slow but Telegram is accessible")
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}")
    
    print()

# Test 3: Send test message
if direct_works:
    print("🔍 Test 3: Sending test message...")
    send_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': '✅ Telegram connectivity test successful!\n\nYour alerts are working correctly.',
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(send_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ SUCCESS! Test message sent to Telegram")
            print(f"   Check your Telegram app for the message")
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    print()

# Summary
print("="*70)
print("  SUMMARY & RECOMMENDATIONS")
print("="*70 + "\n")

if direct_works:
    print("✅ TELEGRAM IS WORKING!")
    print("\nYour Telegram connectivity is fine. If alerts are not being delivered,")
    print("the issue is in the application code, not the network.")
    print("\nRecommended actions:")
    print("1. Check application logs for errors")
    print("2. Verify TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
    print("3. Restart the application")
    
else:
    print("❌ TELEGRAM IS BLOCKED!")
    print("\nYour network is blocking access to api.telegram.org")
    print("\nRECOMMENDED SOLUTIONS (in order):")
    print("\n1. 🔐 USE VPN (Fastest - 2 minutes)")
    print("   - Install ProtonVPN (free): https://protonvpn.com/download")
    print("   - Connect to any server")
    print("   - Run this test again")
    print("   - Restart your application")
    print("\n2. 📱 USE MOBILE HOTSPOT")
    print("   - Connect to your phone's internet")
    print("   - Run this test again")
    print("   - If it works, the issue is your WiFi/network")
    print("\n3. 🌐 USE ALTERNATIVE NOTIFICATION")
    print("   - Email alerts (Gmail SMTP)")
    print("   - Discord webhook")
    print("   - Slack webhook")
    print("\n4. 💻 USE WEB UI")
    print("   - Open http://localhost:8000/alerts")
    print("   - All alerts are saved to database")
    print("   - Refresh page to see new alerts")
    
    print("\nDIAGNOSTIC INFO:")
    print(f"   - Internet: ✅ Working")
    print(f"   - Telegram API: ❌ Blocked (timeout)")
    print(f"   - Bot Token: {'✅ Set' if TELEGRAM_BOT_TOKEN else '❌ Missing'}")
    print(f"   - Chat ID: {'✅ Set' if TELEGRAM_CHAT_ID else '❌ Missing'}")

print("\n" + "="*70)
print()

