import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json

load_dotenv()

access_token = os.getenv('DHAN_ACCESS_TOKEN')
client_id = os.getenv('DHAN_CLIENT_ID')

headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'access-token': access_token,
    'client-id': client_id
}

# Test with recent dates (use actual past dates - September 2024)
to_date = datetime(2024, 9, 15, 15, 30, 0)
from_date = datetime(2024, 9, 11, 9, 15, 0)

# Try different payload formats
payloads_to_test = [
    {
        'name': 'Test 1: String security ID',
        'payload': {
            'securityId': '11536',
            'exchangeSegment': 'NSE_EQ',
            'instrument': 'EQUITY',
            'interval': '1',
            'fromDate': from_date.strftime('%Y-%m-%d %H:%M:%S'),
            'toDate': to_date.strftime('%Y-%m-%d %H:%M:%S')
        }
    },
    {
        'name': 'Test 2: Integer security ID',
        'payload': {
            'securityId': 11536,
            'exchangeSegment': 'NSE_EQ',
            'instrument': 'EQUITY',
            'interval': '1',
            'fromDate': from_date.strftime('%Y-%m-%d %H:%M:%S'),
            'toDate': to_date.strftime('%Y-%m-%d %H:%M:%S')
        }
    },
    {
        'name': 'Test 3: With expiryCode',
        'payload': {
            'securityId': '11536',
            'exchangeSegment': 'NSE_EQ',
            'instrument': 'EQUITY',
            'expiryCode': 0,
            'interval': '1',
            'fromDate': from_date.strftime('%Y-%m-%d %H:%M:%S'),
            'toDate': to_date.strftime('%Y-%m-%d %H:%M:%S')
        }
    }
]

print('Testing Dhan Intraday API...')
print()

for test in payloads_to_test:
    print(f"\n{test['name']}:")
    print(f"Payload: {json.dumps(test['payload'], indent=2)}")

    response = requests.post(
        'https://api.dhan.co/v2/charts/intraday',
        headers=headers,
        json=test['payload'],
        timeout=30
    )

    print(f'Status: {response.status_code}')

    if response.status_code == 200:
        data = response.json()
        if data.get('status') == 'success':
            candles = data.get('data', [])
            print(f'✅ Success! Fetched {len(candles)} candles')
            if candles:
                print('\nFirst 3 candles:')
                for candle in candles[:3]:
                    print(f'  {candle}')
            break  # Stop testing if successful
        else:
            print(f'❌ API returned error: {data}')
    else:
        print(f'Response: {response.text}')

    print('-' * 60)

