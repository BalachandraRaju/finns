#!/usr/bin/env python3
"""
Setup PostgreSQL database for Finns Auto trading application.
"""

import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

def setup_postgresql():
    """Set up PostgreSQL database."""
    load_dotenv()
    
    print('🗄️ SETTING UP POSTGRESQL DATABASE')
    print('=' * 50)
    
    # Database connection parameters
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')
    user = os.getenv('POSTGRES_USER', 'postgres')
    password = os.getenv('POSTGRES_PASSWORD', 'postgres')
    database = os.getenv('POSTGRES_DB', 'finns_auto')
    
    print(f'📊 Host: {host}:{port}')
    print(f'👤 User: {user}')
    print(f'🗄️ Database: {database}')
    
    try:
        # First, connect to default postgres database to create our database
        print('\n🔗 Connecting to PostgreSQL...')
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database='postgres'  # Connect to default database first
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print('✅ Connected to PostgreSQL successfully!')
        
        # Check if our database exists
        cursor.execute('SELECT 1 FROM pg_database WHERE datname = %s', (database,))
        exists = cursor.fetchone()
        
        if not exists:
            print(f'📊 Creating database: {database}')
            cursor.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(database)))
            print(f'✅ Database {database} created successfully!')
        else:
            print(f'✅ Database {database} already exists')
        
        cursor.close()
        conn.close()
        
        # Now test connection to our database
        print(f'\n🧪 Testing connection to {database}...')
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
        print(f'✅ PostgreSQL version: {version[0]}')
        
        cursor.close()
        conn.close()
        
        print('\n🎉 PostgreSQL setup completed successfully!')
        return True
        
    except psycopg2.Error as e:
        print(f'❌ PostgreSQL error: {e}')
        print('💡 Make sure PostgreSQL is installed and running')
        print('🔧 Install: brew install postgresql')
        print('🚀 Start: brew services start postgresql')
        return False
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

def test_application_with_postgresql():
    """Test application with PostgreSQL."""
    print('\n🧪 TESTING APPLICATION WITH POSTGRESQL')
    print('=' * 50)
    
    try:
        from app.db import DATABASE_URL, engine, SessionLocal
        print(f'📊 Database URL: {DATABASE_URL}')
        
        # Test connection
        with engine.connect() as conn:
            print('✅ SQLAlchemy connection successful!')
        
        # Test session
        db = SessionLocal()
        try:
            print('✅ Database session created successfully!')
        finally:
            db.close()
        
        # Create tables
        from app.models import Base
        Base.metadata.create_all(bind=engine)
        print('✅ Database tables created/verified!')
        
        # Check existing data
        from app.models import Candle, LTPData
        db = SessionLocal()
        try:
            candle_count = db.query(Candle).count()
            ltp_count = db.query(LTPData).count()
            print(f'📊 Existing data: {candle_count} candles, {ltp_count} LTP records')
        finally:
            db.close()
        
        print('✅ Application works with PostgreSQL!')
        return True
        
    except Exception as e:
        print(f'❌ Application test failed: {e}')
        return False

if __name__ == "__main__":
    print("🚀 PostgreSQL Setup for Finns Auto")
    print("=" * 50)
    
    # Step 1: Setup PostgreSQL
    if setup_postgresql():
        # Step 2: Test application
        if test_application_with_postgresql():
            print("\n🎉 PostgreSQL setup completed successfully!")
            print("📊 Application is ready to use PostgreSQL database")
        else:
            print("\n⚠️ PostgreSQL setup completed but application needs attention")
    else:
        print("\n❌ PostgreSQL setup failed")
        print("💡 Please install and start PostgreSQL:")
        print("   brew install postgresql")
        print("   brew services start postgresql")
