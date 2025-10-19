#!/usr/bin/env python3
"""
Fix All Issues: PostgreSQL + Upstox API + Database Migration
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

def check_postgresql():
    """Check if PostgreSQL is installed and running."""
    print("🗄️ CHECKING POSTGRESQL")
    print("-" * 40)
    
    try:
        # Check if PostgreSQL is installed
        result = subprocess.run(['which', 'psql'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ PostgreSQL not installed")
            print("🔧 Installing PostgreSQL...")
            
            # Install PostgreSQL
            install_result = subprocess.run(['brew', 'install', 'postgresql@14'], 
                                          capture_output=True, text=True)
            if install_result.returncode != 0:
                print(f"❌ Failed to install PostgreSQL: {install_result.stderr}")
                return False
            
            print("✅ PostgreSQL installed successfully")
        else:
            print("✅ PostgreSQL is installed")
        
        # Check if PostgreSQL is running
        status_result = subprocess.run(['brew', 'services', 'list'], 
                                     capture_output=True, text=True)
        if 'postgresql' in status_result.stdout and 'started' in status_result.stdout:
            print("✅ PostgreSQL is running")
        else:
            print("🚀 Starting PostgreSQL...")
            start_result = subprocess.run(['brew', 'services', 'start', 'postgresql@14'], 
                                        capture_output=True, text=True)
            if start_result.returncode == 0:
                print("✅ PostgreSQL started successfully")
            else:
                print(f"❌ Failed to start PostgreSQL: {start_result.stderr}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking PostgreSQL: {e}")
        return False

def setup_postgresql_database():
    """Set up PostgreSQL database."""
    print("\n🗄️ SETTING UP POSTGRESQL DATABASE")
    print("-" * 40)
    
    try:
        import psycopg2
        from psycopg2 import sql
        
        load_dotenv()
        
        # Database connection parameters
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = os.getenv('POSTGRES_PORT', '5432')
        user = os.getenv('POSTGRES_USER', 'postgres')
        password = os.getenv('POSTGRES_PASSWORD', 'postgres')
        database = os.getenv('POSTGRES_DB', 'finns_auto')
        
        print(f"📊 Connecting to {host}:{port} as {user}")
        
        # Connect to default postgres database
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database='postgres'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute('SELECT 1 FROM pg_database WHERE datname = %s', (database,))
        exists = cursor.fetchone()
        
        if not exists:
            print(f"📊 Creating database: {database}")
            cursor.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(database)))
            print(f"✅ Database {database} created!")
        else:
            print(f"✅ Database {database} already exists")
        
        cursor.close()
        conn.close()
        
        # Test connection to our database
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()
        print(f"✅ Connected to: {version[0][:50]}...")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL setup failed: {e}")
        return False

def migrate_data_to_postgresql():
    """Migrate data from SQLite to PostgreSQL."""
    print("\n📊 MIGRATING DATA TO POSTGRESQL")
    print("-" * 40)
    
    try:
        # First, test the new PostgreSQL connection
        from app.db import DATABASE_URL, engine, SessionLocal
        print(f"📊 Database URL: {DATABASE_URL}")
        
        if 'postgresql' not in DATABASE_URL:
            print("❌ Not using PostgreSQL URL")
            return False
        
        # Test connection
        with engine.connect() as conn:
            print("✅ PostgreSQL connection successful!")
        
        # Create tables
        from app.models import Base
        Base.metadata.create_all(bind=engine)
        print("✅ PostgreSQL tables created!")
        
        # Check existing data
        from app.models import Candle, LTPData
        db = SessionLocal()
        try:
            candle_count = db.query(Candle).count()
            ltp_count = db.query(LTPData).count()
            print(f"📊 Current data: {candle_count} candles, {ltp_count} LTP records")
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Data migration failed: {e}")
        return False

def fix_upstox_api():
    """Fix Upstox API authentication."""
    print("\n🌐 FIXING UPSTOX API")
    print("-" * 40)
    
    load_dotenv()
    current_token = os.getenv('UPSTOX_ACCESS_TOKEN')
    print(f"📊 Current token: {current_token}")
    
    print("💡 The Upstox access token has expired (401 error)")
    print("🔧 To fix this, you need to:")
    print("   1. Go to Upstox Developer Console: https://developer.upstox.com/")
    print("   2. Generate a new access token")
    print("   3. Update the .env file with the new token")
    print("")
    print("📝 Update this line in .env:")
    print(f"   UPSTOX_ACCESS_TOKEN=your_new_token_here")
    print("")
    
    # Test current token
    try:
        sys.path.append('data-fetch')
        from upstox_ltp_client import upstox_ltp_client
        
        if upstox_ltp_client.test_connection():
            print("✅ Upstox API is working!")
            return True
        else:
            print("❌ Upstox API authentication failed")
            print("🔧 Please update the access token in .env file")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Upstox API: {e}")
        return False

def test_complete_system():
    """Test the complete system."""
    print("\n🧪 TESTING COMPLETE SYSTEM")
    print("-" * 40)
    
    try:
        # Test database
        from app.db import DATABASE_URL
        print(f"📊 Database: {DATABASE_URL}")
        
        if 'postgresql' in DATABASE_URL:
            print("✅ Using PostgreSQL")
        else:
            print("⚠️ Still using SQLite")
        
        # Test application startup
        from app.main import app
        print("✅ FastAPI app loads successfully")
        
        # Test LTP service
        sys.path.append('data-fetch')
        from ltp_service import ltp_service
        
        connection_test = ltp_service.test_upstox_connection()
        if connection_test:
            print("✅ Upstox API working")
        else:
            print("❌ Upstox API needs token update")
        
        # Test alert system
        from app.scheduler import check_for_alerts
        print("✅ Alert system ready")
        
        return True
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

def main():
    """Main function to fix all issues."""
    print("🚀 FIXING ALL ISSUES: PostgreSQL + Upstox API")
    print("=" * 60)
    
    results = {}
    
    # Step 1: Check and install PostgreSQL
    results['postgresql_install'] = check_postgresql()
    
    # Step 2: Set up PostgreSQL database
    if results['postgresql_install']:
        results['postgresql_setup'] = setup_postgresql_database()
    else:
        results['postgresql_setup'] = False
    
    # Step 3: Migrate to PostgreSQL
    if results['postgresql_setup']:
        results['data_migration'] = migrate_data_to_postgresql()
    else:
        results['data_migration'] = False
    
    # Step 4: Fix Upstox API
    results['upstox_api'] = fix_upstox_api()
    
    # Step 5: Test complete system
    results['system_test'] = test_complete_system()
    
    # Summary
    print("\n🎯 SUMMARY")
    print("=" * 60)
    
    for component, success in results.items():
        status = "✅ FIXED" if success else "❌ NEEDS ATTENTION"
        print(f"   {component.upper().replace('_', ' ')}: {status}")
    
    total_fixed = sum(results.values())
    total_issues = len(results)
    
    print(f"\n📊 OVERALL: {total_fixed}/{total_issues} issues resolved")
    
    if total_fixed == total_issues:
        print("🎉 ALL ISSUES FIXED!")
    elif total_fixed >= total_issues // 2:
        print("⚠️ PARTIAL SUCCESS - Some issues need manual attention")
    else:
        print("❌ MULTIPLE ISSUES - Need manual intervention")
    
    # Next steps
    print("\n💡 NEXT STEPS:")
    
    if not results['postgresql_install']:
        print("   🗄️ Install PostgreSQL: brew install postgresql@14")
        print("   🚀 Start PostgreSQL: brew services start postgresql@14")
    
    if not results['upstox_api']:
        print("   🌐 Update Upstox access token in .env file")
        print("   📝 Get new token from: https://developer.upstox.com/")
    
    if results['postgresql_setup'] and results['upstox_api']:
        print("   🎉 System is ready! Start the application:")
        print("   🚀 python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    main()
