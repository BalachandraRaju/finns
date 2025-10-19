#!/usr/bin/env python3
"""
Check current system status and identify issues.
"""

import os
import sys
from dotenv import load_dotenv

def main():
    print('🔍 CHECKING CURRENT SYSTEM STATUS')
    print('=' * 50)
    
    # Check current database
    try:
        from app.db import DATABASE_URL
        print(f'📊 Current database: {DATABASE_URL}')
        
        if 'postgresql' in DATABASE_URL:
            print('✅ Using PostgreSQL')
        else:
            print('⚠️ Using SQLite (should switch to PostgreSQL)')
            
    except Exception as e:
        print(f'❌ Database check failed: {e}')
    
    # Check Upstox token
    load_dotenv()
    token = os.getenv('UPSTOX_ACCESS_TOKEN')
    if token:
        print(f'🌐 Upstox token: {token[:20]}...')
    else:
        print('❌ No Upstox token found')
    
    # Check PostgreSQL availability
    try:
        import psycopg2
        print('✅ psycopg2 installed')
    except ImportError:
        print('❌ psycopg2 not installed')
    
    # Test Upstox API
    try:
        sys.path.append('data-fetch')
        from upstox_ltp_client import upstox_ltp_client
        
        if upstox_ltp_client.test_connection():
            print('✅ Upstox API working')
        else:
            print('❌ Upstox API failed (401 authentication error)')
    except Exception as e:
        print(f'❌ Upstox API test error: {e}')
    
    print('\n💡 ISSUES TO FIX:')
    print('1. ❌ Switch from SQLite to PostgreSQL')
    print('2. ❌ Fix Upstox API authentication (401 error)')
    print('3. ❌ Ensure LTP and history APIs work')
    
    print('\n🔧 SOLUTIONS:')
    print('1. Install PostgreSQL and update .env')
    print('2. Get new Upstox access token')
    print('3. Test both APIs after fixing authentication')

if __name__ == "__main__":
    main()
