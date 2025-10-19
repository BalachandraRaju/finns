import pyotp
import time
from SmartApi import SmartConnect

# Your credentials
API_KEY = "S40dIrb6"
USERNAME = "B6140929"
PASSWORD = "1841"
TOTP_TOKEN = "LMZO3OBSHKK5JJPJ2X7U2GWGRU"

def minimal_test():
    """Minimal test with single API call"""
    print("--- Minimal Angel One Test ---")
    
    try:
        # Initialize
        client = SmartConnect(API_KEY)
        print("✅ Client initialized")
        
        # Wait before authentication
        print("⏳ Waiting 5 seconds before authentication...")
        time.sleep(5)
        
        # Generate TOTP
        totp = pyotp.TOTP(TOTP_TOKEN).now()
        print(f"Generated TOTP: {totp}")
        
        # Authenticate
        print("🔐 Attempting authentication...")
        data = client.generateSession(USERNAME, PASSWORD, totp)
        
        if data.get('status'):
            print("✅ Authentication successful!")
            print(f"User: {data.get('data', {}).get('clientname', 'Unknown')}")
            
            # Just get profile info (minimal API call)
            try:
                profile = client.getProfile(data['data']['refreshToken'])
                if profile.get('status'):
                    print("✅ Profile fetched successfully")
                    print(f"Client ID: {profile['data']['clientcode']}")
                else:
                    print(f"❌ Profile fetch failed: {profile}")
            except Exception as e:
                print(f"❌ Profile fetch error: {e}")
                
        else:
            print(f"❌ Authentication failed: {data}")
            
    except Exception as e:
        if 'rate' in str(e).lower() or 'access denied' in str(e).lower():
            print(f"❌ Rate limit error: {e}")
            print("💡 Please wait 10-15 minutes before trying again")
        else:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    minimal_test()