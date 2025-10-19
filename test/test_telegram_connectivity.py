#!/usr/bin/env python3
"""
Telegram Connectivity Diagnostic Tool
Tests network connectivity to Telegram API and diagnoses issues.
"""

import requests
import time
import socket
import sys

# Telegram Bot Configuration
BOT_TOKEN = "6224129302:AAG8iAT2H7SBfvhAi2sB-SLAwHCguuZ1oGE"
CHAT_ID = "1085019965"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_internet_connectivity():
    """Test basic internet connectivity."""
    print_header("TEST 1: Internet Connectivity")
    
    test_urls = [
        "https://www.google.com",
        "https://www.cloudflare.com",
        "https://1.1.1.1"
    ]
    
    for url in test_urls:
        try:
            start = time.time()
            response = requests.get(url, timeout=10)
            elapsed = time.time() - start
            
            if response.status_code == 200:
                print(f"✅ {url}: OK ({elapsed:.2f}s)")
            else:
                print(f"⚠️ {url}: Status {response.status_code}")
        except Exception as e:
            print(f"❌ {url}: FAILED - {e}")
    
    return True

def test_dns_resolution():
    """Test DNS resolution for Telegram API."""
    print_header("TEST 2: DNS Resolution")
    
    hostname = "api.telegram.org"
    
    try:
        ip_addresses = socket.gethostbyname_ex(hostname)
        print(f"✅ DNS Resolution: SUCCESS")
        print(f"   Hostname: {hostname}")
        print(f"   IP Addresses: {ip_addresses[2]}")
        return True
    except socket.gaierror as e:
        print(f"❌ DNS Resolution: FAILED")
        print(f"   Error: {e}")
        return False

def test_telegram_api_reachability():
    """Test if Telegram API is reachable."""
    print_header("TEST 3: Telegram API Reachability")
    
    url = f"{BASE_URL}/getMe"
    
    print(f"Testing: {url}")
    print(f"Timeout: 30 seconds")
    print()
    
    try:
        start = time.time()
        response = requests.get(url, timeout=30)
        elapsed = time.time() - start
        
        print(f"✅ SUCCESS!")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                print(f"   Bot Username: @{bot_info.get('username')}")
                print(f"   Bot Name: {bot_info.get('first_name')}")
                return True
        else:
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT ERROR")
        print(f"   The request took longer than 30 seconds")
        print(f"   Possible causes:")
        print(f"     • Network/Firewall blocking Telegram")
        print(f"     • ISP blocking Telegram")
        print(f"     • Very slow internet connection")
        return False
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ CONNECTION ERROR")
        print(f"   Error: {e}")
        print(f"   Possible causes:")
        print(f"     • No internet connection")
        print(f"     • DNS resolution failed")
        print(f"     • Telegram API is down")
        print(f"     • Firewall blocking connection")
        return False
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR")
        print(f"   Error: {e}")
        return False

def test_send_message():
    """Test sending a message via Telegram."""
    print_header("TEST 4: Send Test Message")
    
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": "🧪 Telegram Connectivity Test\n\nThis is a test message to verify connectivity.\n\n✅ If you see this, Telegram is working!",
        "parse_mode": "HTML"
    }
    
    print(f"Sending test message to chat ID: {CHAT_ID}")
    print()
    
    try:
        start = time.time()
        response = requests.post(url, json=payload, timeout=30)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            print(f"✅ MESSAGE SENT SUCCESSFULLY!")
            print(f"   Response Time: {elapsed:.2f}s")
            print(f"   Check your Telegram app for the test message")
            return True
        else:
            print(f"❌ FAILED TO SEND MESSAGE")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT ERROR - Message not sent")
        return False
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ CONNECTION ERROR - Message not sent")
        print(f"   Error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ ERROR - Message not sent")
        print(f"   Error: {e}")
        return False

def print_diagnostics():
    """Print diagnostic information."""
    print_header("DIAGNOSTIC INFORMATION")
    
    print("Network Configuration:")
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"   Hostname: {hostname}")
        print(f"   Local IP: {local_ip}")
    except:
        print("   Unable to get network info")
    
    print()
    print("Telegram Configuration:")
    print(f"   Bot Token: {BOT_TOKEN[:20]}...")
    print(f"   Chat ID: {CHAT_ID}")
    print(f"   API URL: {BASE_URL}")

def print_recommendations(results):
    """Print recommendations based on test results."""
    print_header("RECOMMENDATIONS")
    
    internet_ok = results.get('internet', False)
    dns_ok = results.get('dns', False)
    api_ok = results.get('api', False)
    message_ok = results.get('message', False)
    
    if internet_ok and dns_ok and api_ok and message_ok:
        print("✅ ALL TESTS PASSED!")
        print("   Telegram integration is working correctly.")
        print("   If you're still experiencing issues, check application logs.")
        return
    
    print("⚠️ ISSUES DETECTED:")
    print()
    
    if not internet_ok:
        print("❌ Internet Connectivity Issue")
        print("   • Check your internet connection")
        print("   • Verify network cables/WiFi")
        print("   • Try restarting your router")
        print()
    
    if not dns_ok:
        print("❌ DNS Resolution Issue")
        print("   • Check DNS settings")
        print("   • Try using Google DNS (8.8.8.8, 8.8.4.4)")
        print("   • Try using Cloudflare DNS (1.1.1.1)")
        print()
    
    if internet_ok and dns_ok and not api_ok:
        print("❌ Telegram API Blocked")
        print("   • Your network/ISP may be blocking Telegram")
        print("   • Try using a VPN")
        print("   • Check corporate firewall settings")
        print("   • Try from mobile data to confirm")
        print()
    
    if api_ok and not message_ok:
        print("❌ Message Sending Issue")
        print("   • Check bot token and chat ID")
        print("   • Verify bot has permission to send messages")
        print("   • Check if chat exists")
        print()

def main():
    """Run all diagnostic tests."""
    print("\n" + "=" * 70)
    print("  TELEGRAM CONNECTIVITY DIAGNOSTIC TOOL")
    print("  Testing network connectivity to Telegram API")
    print("=" * 70)
    
    results = {}
    
    # Run tests
    results['internet'] = test_internet_connectivity()
    results['dns'] = test_dns_resolution()
    results['api'] = test_telegram_api_reachability()
    
    if results['api']:
        results['message'] = test_send_message()
    else:
        results['message'] = False
        print_header("TEST 4: Send Test Message")
        print("⏭️ SKIPPED - API not reachable")
    
    # Print diagnostics
    print_diagnostics()
    
    # Print recommendations
    print_recommendations(results)
    
    # Summary
    print_header("SUMMARY")
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    print()
    
    if passed_tests == total_tests:
        print("✅ All tests passed! Telegram integration is working.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. See recommendations above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

