import requests
import datetime
import json

# --- IMPORTANT ---
# You need a valid access token from Upstox to run this.
# Replace 'YOUR_ACCESS_TOKEN' with your actual token.
ACCESS_TOKEN = '5998804c-ac2a-4de0-892d-972193845837'

# Test parameters
instrument_key = "NSE_EQ|INE335Y01020"  # The problematic instrument
interval = "1minute"
today = datetime.date.today().strftime('%Y-%m-%d')

print(f"Testing intraday data fetching for {today}")
print(f"Instrument: {instrument_key}")
print(f"Interval: {interval}")
print("="*60)

# Test 1: Historical data for today
print("\n1. Testing Historical Data API for today:")
historical_url = f"https://api-v2.upstox.com/historical-candle/{instrument_key}/{interval}/{today}"
print(f"URL: {historical_url}")

# Test 2: Intraday data API
print("\n2. Testing Intraday Data API:")
intraday_url = f"https://api-v2.upstox.com/historical-candle/intraday/{instrument_key}/{interval}"
print(f"URL: {intraday_url}")

headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {ACCESS_TOKEN}'
}

def test_api_endpoint(url, description):
    """Test a specific API endpoint and return the results."""
    print(f"\n{description}")
    print(f"URL: {url}")
    print("-" * 50)

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        print(f"✅ SUCCESS - Status Code: {response.status_code}")
        data = response.json()

        if data.get('status') == 'success' and data.get('data', {}).get('candles'):
            candles = data['data']['candles']
            print(f"📊 Found {len(candles)} candles")

            # Show first few candles
            print("📈 Sample data (first 3 candles):")
            for i, candle in enumerate(candles[:3]):
                timestamp, open_price, high, low, close, volume, oi = candle
                print(f"  {i+1}. {timestamp} | O:{open_price} H:{high} L:{low} C:{close} V:{volume}")

            # Show latest candle
            if len(candles) > 3:
                latest = candles[-1]
                timestamp, open_price, high, low, close, volume, oi = latest
                print(f"🕐 Latest: {timestamp} | O:{open_price} H:{high} L:{low} C:{close} V:{volume}")

        else:
            print(f"⚠️  No candle data found. Response: {json.dumps(data, indent=2)}")

        return True, data

    except requests.exceptions.HTTPError as errh:
        print(f"❌ HTTP Error - Status Code: {errh.response.status_code}")
        print(f"Error Response: {errh.response.text}")
        return False, None
    except requests.exceptions.RequestException as err:
        print(f"❌ Request Exception: {err}")
        return False, None

# --- Main Testing ---
if ACCESS_TOKEN == 'YOUR_ACCESS_TOKEN':
    print("\n⚠️  WARNING: Please replace 'YOUR_ACCESS_TOKEN' with your actual Upstox access token.")
else:
    print(f"\n🚀 Starting API tests with token: {ACCESS_TOKEN[:10]}...")

    # Test 1: Historical data for today
    success1, data1 = test_api_endpoint(historical_url, "🔍 Test 1: Historical Data for Today")

    # Test 2: Intraday data
    success2, data2 = test_api_endpoint(intraday_url, "🔍 Test 2: Current Intraday Data")

    # Summary
    print("\n" + "="*60)
    print("📋 SUMMARY:")
    print(f"Historical Data API: {'✅ Working' if success1 else '❌ Failed'}")
    print(f"Intraday Data API: {'✅ Working' if success2 else '❌ Failed'}")

    if success1 and success2:
        print("\n🎉 Both APIs are working! Intraday data is available.")
    elif success1:
        print("\n⚠️  Only historical data is working. Intraday API may be down or have different requirements.")
    elif success2:
        print("\n⚠️  Only intraday data is working. Historical API may have issues.")
    else:
        print("\n❌ Both APIs failed. Check your access token and network connection.")