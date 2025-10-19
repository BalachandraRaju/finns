#!/usr/bin/env python3
"""
Database migration script to add LTP and data sync tables.
Run this script to create the new tables for real-time data collection.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.db import DATABASE_URL, Base
from app.models import LTPData, DataSyncStatus
from logzero import logger

def create_ltp_tables():
    """Create LTP and data sync tables."""
    try:
        logger.info("🔧 Creating database engine...")
        engine = create_engine(DATABASE_URL)
        
        logger.info("📊 Creating LTP and data sync tables...")
        
        # Create all tables defined in models
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Successfully created LTP and data sync tables")
        
        # Verify tables were created
        with engine.connect() as conn:
            # Check if ltp_data table exists
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='ltp_data'"))
            if result.fetchone():
                logger.info("✅ ltp_data table created successfully")
            else:
                logger.error("❌ ltp_data table not found")
            
            # Check if data_sync_status table exists
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='data_sync_status'"))
            if result.fetchone():
                logger.info("✅ data_sync_status table created successfully")
            else:
                logger.error("❌ data_sync_status table not found")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating LTP tables: {e}")
        return False

def verify_tables():
    """Verify that all required tables exist."""
    try:
        engine = create_engine(DATABASE_URL)
        
        required_tables = ['ltp_data', 'data_sync_status', 'candles']
        
        with engine.connect() as conn:
            for table_name in required_tables:
                result = conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"))
                if result.fetchone():
                    logger.info(f"✅ Table '{table_name}' exists")
                else:
                    logger.error(f"❌ Table '{table_name}' not found")
                    return False
        
        logger.info("✅ All required tables verified")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verifying tables: {e}")
        return False

def show_table_info():
    """Show information about the created tables."""
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Show LTP data table structure
            logger.info("📊 LTP Data table structure:")
            result = conn.execute(text("PRAGMA table_info(ltp_data)"))
            for row in result:
                logger.info(f"   {row[1]} ({row[2]})")
            
            # Show data sync status table structure
            logger.info("📊 Data Sync Status table structure:")
            result = conn.execute(text("PRAGMA table_info(data_sync_status)"))
            for row in result:
                logger.info(f"   {row[1]} ({row[2]})")
        
    except Exception as e:
        logger.error(f"❌ Error showing table info: {e}")

if __name__ == "__main__":
    print("🔧 Database Migration: Adding LTP and Data Sync Tables")
    print("=" * 60)
    
    # Check if database file exists
    if not os.path.exists("historical_data.db"):
        logger.warning("⚠️ Database file not found. It will be created.")
    
    # Create tables
    if create_ltp_tables():
        logger.info("✅ Migration completed successfully")
        
        # Verify tables
        if verify_tables():
            logger.info("✅ Table verification passed")
            
            # Show table info
            show_table_info()
            
            print("\n🎉 Migration completed successfully!")
            print("💡 You can now run the data fetching tests:")
            print("   python data-fetch/test_data_fetch.py")
        else:
            logger.error("❌ Table verification failed")
            sys.exit(1)
    else:
        logger.error("❌ Migration failed")
        sys.exit(1)
