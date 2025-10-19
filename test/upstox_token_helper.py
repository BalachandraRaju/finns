#!/usr/bin/env python3
"""
Upstox Token Helper - Alternative methods to get access token
"""

import requests
import webbrowser
from urllib.parse import urlencode
import os
from dotenv import load_dotenv

def get_upstox_auth_url():
    """Generate Upstox authorization URL for manual token generation."""
    load_dotenv()
    
    # Your app details from the screenshot
    client_id = "5998804c-ac2a-4de0-892d-972193845837"  # Your API Key
    redirect_uri = "https://127.0.0.1"  # Default redirect URI
    
    auth_params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'state': 'finns_app'
    }
    
    auth_url = f"https://api.upstox.com/v2/login/authorization/dialog?{urlencode(auth_params)}"
    
    print("🌐 UPSTOX TOKEN GENERATION HELPER")
    print("=" * 50)
    print("Since the web console isn't working, try this manual method:")
    print()
    print("1. Copy this URL and open in browser:")
    print(f"   {auth_url}")
    print()
    print("2. Login with your Upstox credentials")
    print("3. After authorization, you'll be redirected to a URL like:")
    print("   https://127.0.0.1/?code=YOUR_AUTH_CODE&state=finns_app")
    print()
    print("4. Copy the 'code' parameter from the URL")
    print("5. Use that code to get access token")
    print()
    
    # Open URL automatically
    try:
        webbrowser.open(auth_url)
        print("✅ Browser opened automatically")
    except:
        print("⚠️ Please copy the URL manually")
    
    return auth_url

def exchange_code_for_token(auth_code):
    """Exchange authorization code for access token."""
    load_dotenv()
    
    client_id = "5998804c-ac2a-4de0-892d-972193845837"
    client_secret = "5bs6qe7efs"  # Your API Secret from screenshot
    redirect_uri = "https://127.0.0.1"
    
    token_url = "https://api.upstox.com/v2/login/authorization/token"
    
    data = {
        'code': auth_code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    try:
        response = requests.post(token_url, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')
            
            print("✅ Token generated successfully!")
            print(f"Access Token: {access_token}")
            
            # Update .env file
            update_env_token(access_token)
            
            return access_token
        else:
            print(f"❌ Token generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def update_env_token(new_token):
    """Update .env file with new token."""
    try:
        # Read current .env
        with open('.env', 'r') as f:
            lines = f.readlines()
        
        # Update token line
        updated_lines = []
        token_updated = False
        
        for line in lines:
            if line.startswith('UPSTOX_ACCESS_TOKEN='):
                updated_lines.append(f'UPSTOX_ACCESS_TOKEN={new_token}\n')
                token_updated = True
            else:
                updated_lines.append(line)
        
        # If token line doesn't exist, add it
        if not token_updated:
            updated_lines.append(f'UPSTOX_ACCESS_TOKEN={new_token}\n')
        
        # Write back to .env
        with open('.env', 'w') as f:
            f.writelines(updated_lines)
        
        print("✅ .env file updated with new token")
        
    except Exception as e:
        print(f"❌ Error updating .env: {e}")

def test_token(token):
    """Test if the token works."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get('https://api.upstox.com/v2/user/profile', headers=headers)
        
        if response.status_code == 200:
            print("✅ Token is working!")
            return True
        else:
            print(f"❌ Token test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Token test error: {e}")
        return False

def main():
    """Main function for token generation."""
    print("🚀 UPSTOX TOKEN GENERATION")
    print("=" * 40)
    
    choice = input("Choose option:\n1. Generate auth URL\n2. Exchange code for token\n3. Test existing token\nEnter (1/2/3): ")
    
    if choice == '1':
        get_upstox_auth_url()
        
    elif choice == '2':
        auth_code = input("Enter authorization code from redirect URL: ")
        if auth_code:
            exchange_code_for_token(auth_code)
        else:
            print("❌ No code provided")
            
    elif choice == '3':
        load_dotenv()
        token = os.getenv('UPSTOX_ACCESS_TOKEN')
        if token:
            test_token(token)
        else:
            print("❌ No token found in .env")
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
