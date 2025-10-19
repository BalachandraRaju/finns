import os
import requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('UPSTOX_ACCESS_TOKEN')

print('🌐 TESTING NEW UPSTOX ACCESS TOKEN')
print('=' * 50)
print(f'📊 Token: {token}')

headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/json'
}

try:
    response = requests.get('https://api.upstox.com/v2/user/profile', headers=headers, timeout=10)
    
    if response.status_code == 200:
        print('✅ Upstox API authentication successful!')
        user_data = response.json()
        user_name = user_data.get('data', {}).get('user_name', 'Unknown')
        print(f'👤 User: {user_name}')
        print('🎉 TOKEN IS WORKING!')
    else:
        print(f'❌ Upstox API failed: {response.status_code}')
        print(f'Response: {response.text}')
        
except Exception as e:
    print(f'❌ Error: {e}')
