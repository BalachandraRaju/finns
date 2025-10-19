"""
Dhan API Authentication Helper
Helps you set up and test Dhan API authentication.
"""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()


def test_dhan_connection():
    """Test Dhan API connection with current credentials."""
    print("\n" + "="*70)
    print("🔐 DHAN API AUTHENTICATION TEST")
    print("="*70 + "\n")
    
    client_id = os.getenv("DHAN_CLIENT_ID")
    access_token = os.getenv("DHAN_ACCESS_TOKEN")
    
    print(f"📋 Client ID: {client_id}")
    print(f"🔑 Access Token: {access_token[:20]}..." if access_token and len(access_token) > 20 else f"🔑 Access Token: {access_token}")
    print()
    
    if not client_id:
        print("❌ DHAN_CLIENT_ID not found in .env file")
        return False
    
    if not access_token or access_token == "your_access_token_here":
        print("❌ DHAN_ACCESS_TOKEN not set in .env file")
        print("\n📝 To get your access token:")
        print("   1. Go to https://web.dhan.co")
        print("   2. Login to your account")
        print("   3. Click on 'My Profile' → 'Access DhanHQ APIs'")
        print("   4. Generate 'Access Token' (valid for 24 hours)")
        print("   5. Copy the token and update DHAN_ACCESS_TOKEN in .env file")
        print()
        return False
    
    # Test API connection
    try:
        print("🧪 Testing API connection...")
        
        headers = {
            'access-token': access_token,
            'Accept': 'application/json'
        }
        
        response = requests.get(
            'https://api.dhan.co/v2/profile',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ AUTHENTICATION SUCCESSFUL!\n")
            print("📊 Account Details:")
            print(f"   Client ID: {data.get('dhanClientId', 'N/A')}")
            print(f"   Token Validity: {data.get('tokenValidity', 'N/A')}")
            print(f"   Active Segments: {data.get('activeSegment', 'N/A')}")
            print(f"   DDPI Status: {data.get('ddpi', 'N/A')}")
            print(f"   Data Plan: {data.get('dataPlan', 'N/A')}")
            print(f"   Data Validity: {data.get('dataValidity', 'N/A')}")
            print()
            
            # Check if data plan is active
            if data.get('dataPlan') != 'Active':
                print("⚠️  WARNING: Data Plan is not active!")
                print("   You need an active Data API subscription to fetch market data.")
                print("   Please subscribe to Data APIs from Dhan platform.")
                print()
            
            return True
        else:
            print(f"\n❌ AUTHENTICATION FAILED!")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            print()
            
            if response.status_code == 401:
                print("💡 Your access token may have expired (24-hour validity).")
                print("   Please generate a new token from https://web.dhan.co")
                print()
            
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print()
        return False


def show_instructions():
    """Show detailed instructions for setting up Dhan API."""
    print("\n" + "="*70)
    print("📚 DHAN API SETUP INSTRUCTIONS")
    print("="*70 + "\n")
    
    print("STEP 1: Get Your Access Token")
    print("-" * 70)
    print("1. Open your browser and go to: https://web.dhan.co")
    print("2. Login with your Dhan credentials")
    print("3. Click on your profile icon (top right)")
    print("4. Select 'Access DhanHQ APIs'")
    print("5. Click on 'Generate Access Token'")
    print("6. Copy the generated token (valid for 24 hours)")
    print()
    
    print("STEP 2: Update .env File")
    print("-" * 70)
    print("1. Open the .env file in your project root")
    print("2. Find the line: DHAN_ACCESS_TOKEN=your_access_token_here")
    print("3. Replace 'your_access_token_here' with your actual token")
    print("4. Save the file")
    print()
    
    print("STEP 3: Verify Data API Subscription")
    print("-" * 70)
    print("1. Make sure you have an active Data API subscription")
    print("2. This is required to fetch LTP and market data")
    print("3. Subscribe from Dhan platform if not already subscribed")
    print()
    
    print("STEP 4: Run This Script Again")
    print("-" * 70)
    print("Run: python dhan_auth_helper.py")
    print()
    
    print("="*70 + "\n")


def main():
    """Main function."""
    print("\n🚀 Dhan API Authentication Helper\n")
    
    # Test connection
    success = test_dhan_connection()
    
    if not success:
        show_instructions()
        sys.exit(1)
    else:
        print("="*70)
        print("✅ You're all set! Dhan API is ready to use.")
        print("="*70 + "\n")
        
        print("📝 Next Steps:")
        print("   1. Run: python data-fetch/dhan_ltp_client.py")
        print("      (This will test LTP data fetching)")
        print()
        print("   2. Download Dhan instrument list to map symbols to security IDs")
        print("      URL: https://images.dhan.co/api-data/api-scrip-master.csv")
        print()
        print("   3. Integrate with your existing system")
        print()


if __name__ == "__main__":
    main()

