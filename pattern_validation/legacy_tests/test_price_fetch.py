import sys
import pyotp
import time
import pandas as pd
import ta
from SmartApi import SmartConnect

# --- HARDCODE YOUR CREDENTIALS HERE FOR TESTING ---
# IMPORTANT: Replace these placeholder values with your actual credentials.
API_KEY = "S40dIrb6"
USERNAME = "B6140929"
PASSWORD = "1841"
TOTP_TOKEN = "LMZO3OBSHKK5JJPJ2X7U2GWGRU"
# ----------------------------------------------------

def test_fetch_with_hardcoded_credentials(symbols_to_test: list):
    """
    A self-contained script to test Angel One connection and data fetching
    using hardcoded credentials to bypass any .env file issues.
    """
    print("--- Starting Hardcoded Credential Test ---")

    # 1. Initialize Client
    try:
        client = SmartConnect(API_KEY)
    except Exception as e:
        print(f"❌ FAILED: Could not even initialize SmartConnect client. Error: {e}")
        return

    # 2. Generate Session
    try:
        # Some systems have a slight time drift. We'll check the current time and the time 30 seconds ago
        # to account for any delay between when the code is generated and when the server receives it.
        totp_now = pyotp.TOTP(TOTP_TOKEN).now()
        totp_past = pyotp.TOTP(TOTP_TOKEN).at(time.time() - 30)

        print(f"   Generated TOTPs: {totp_now} (current), {totp_past} (30s ago)")

        # First, try with the current TOTP
        data = client.generateSession(USERNAME, PASSWORD, totp_now)

        # If it fails with an invalid TOTP error, try the one from 30 seconds ago
        if data.get('errorcode') == 'AB1050':
             print("   Current TOTP failed, trying previous one...")
             data = client.generateSession(USERNAME, PASSWORD, totp_past)

        if not data.get('status') or not data.get('data'):
            print(f"❌ FAILED: Session generation failed. Server response:")
            print(data)
            return

        print("✅ Session generated successfully.")
        
    except Exception as e:
        print(f"❌ FAILED: An error occurred during session generation: {e}")
        return
        
    # 3. Fetch Data for each symbol
    print(f"\nFetching data for: {symbols_to_test}")
    for symbol in symbols_to_test:
        try:
            # We need the instrument token. For this test, let's hardcode a known one.
            # A full implementation would download the instrument list.
            # Note: This part is simplified and might need adjustment for other symbols.
            # We will use the main app's lookup for a real test. This is just for connection.
            # This is a basic test, let's assume we are testing RELIANCE
            if 'RELIANCE' in symbol:
                token = "2885"
                exchange = "NSE"
            elif 'TCS' in symbol:
                token = "3456" # Example token, might not be correct
                exchange = "NSE"
            else:
                # This is a limitation of a simple test script without the full instrument list.
                print(f"🟡 SKIPPING: Don't have a hardcoded token for {symbol}. This test focuses on login.")
                continue

            historic_param = {
                "exchange": exchange,
                "symboltoken": token,
                "interval": "FIVE_MINUTE",
                "fromdate": "2024-06-20 09:15", # Using a fixed date for consistency
                "todate": "2024-06-25 15:30"
            }
            
            candle_data = client.getCandleData(historic_param)
            
            if candle_data.get('status') and candle_data.get('data'):
                print(f"✅ Successfully fetched data for {symbol}.")
                # print(candle_data['data'][0]) # Uncomment to see first candle
            else:
                print(f"❌ Failed to fetch data for {symbol}. Response: {candle_data}")

        except Exception as e:
            print(f"❌ An error occurred while fetching data for {symbol}: {e}")

    print("\n--- Test Finished ---")


if __name__ == "__main__":
    if "YOUR_API_KEY" in API_KEY:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! PLEASE EDIT THE SCRIPT AND HARDCODE YOUR CREDENTIALS !!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    else:
        if len(sys.argv) > 1:
            symbols = sys.argv[1:]
            test_fetch_with_hardcoded_credentials(symbols)
        else:
            print("Usage: python test_price_fetch.py <STOCK_SYMBOL_1> ...")
            test_fetch_with_hardcoded_credentials(["RELIANCE-EQ"]) # Default test 