#!/usr/bin/env python3
"""
Migration script to add the 'oi' (Open Interest) column to the candles table.
Run this script once to update your existing database.
"""

import sqlite3
import os
from pathlib import Path

def migrate_database():
    """Add the oi column to the candles table if it doesn't exist."""
    
    # Find the database file
    db_path = "historical_data.db"
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found. Creating new database with updated schema.")
        return
    
    print(f"Migrating database: {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the oi column already exists
        cursor.execute("PRAGMA table_info(candles)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'oi' in columns:
            print("Column 'oi' already exists in candles table. No migration needed.")
            conn.close()
            return
        
        print("Adding 'oi' column to candles table...")
        
        # Add the oi column with default value 0
        cursor.execute("ALTER TABLE candles ADD COLUMN oi INTEGER DEFAULT 0")
        
        # Commit the changes
        conn.commit()
        print("Migration completed successfully!")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(candles)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Current columns in candles table: {columns}")
        
    except sqlite3.Error as e:
        print(f"Error during migration: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_database()
