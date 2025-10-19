#!/usr/bin/env python3

import requests

# Test the new Upstox token directly
token = "da521faa-37d7-471b-8fe3-cc419efdc8c5"

print('🌐 TESTING NEW UPSTOX ACCESS TOKEN')
print('=' * 50)
print(f'📊 Token: {token}')

headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/json'
}

try:
    print('🧪 Making API call...')
    response = requests.get('https://api.upstox.com/v2/user/profile', headers=headers, timeout=10)
    
    print(f'📊 Response status: {response.status_code}')
    
    if response.status_code == 200:
        print('✅ Upstox API authentication successful!')
        user_data = response.json()
        print(f'📊 Response data: {user_data}')
        user_name = user_data.get('data', {}).get('user_name', 'Unknown')
        print(f'👤 User: {user_name}')
        print('🎉 TOKEN IS WORKING!')
    else:
        print(f'❌ Upstox API failed: {response.status_code}')
        print(f'Response: {response.text}')
        
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()

print('\n🎯 TESTING LTP API')
print('-' * 30)

# Test LTP API
try:
    # Get LTP for a few stocks
    instrument_keys = [
        'NSE_EQ|INE467B01029',  # TCS
        'NSE_EQ|INE009A01021',  # INFY
        'NSE_EQ|INE002A01018'   # RELIANCE
    ]
    
    ltp_url = 'https://api.upstox.com/v2/market-quote/ltp'
    params = {
        'instrument_key': ','.join(instrument_keys)
    }
    
    print(f'🧪 Testing LTP API with {len(instrument_keys)} stocks...')
    response = requests.get(ltp_url, headers=headers, params=params, timeout=10)
    
    print(f'📊 LTP Response status: {response.status_code}')
    
    if response.status_code == 200:
        print('✅ LTP API working!')
        ltp_data = response.json()
        print(f'📊 LTP data received for {len(ltp_data.get("data", {}))} stocks')
        
        # Show sample LTP data
        for key, data in ltp_data.get('data', {}).items():
            ltp = data.get('last_price', 'N/A')
            print(f'   💰 {key}: ₹{ltp}')
            
    else:
        print(f'❌ LTP API failed: {response.status_code}')
        print(f'Response: {response.text}')
        
except Exception as e:
    print(f'❌ LTP API Error: {e}')
    import traceback
    traceback.print_exc()

print('\n🎉 TOKEN TEST COMPLETE!')
