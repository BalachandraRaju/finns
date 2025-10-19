"""
Create PKScreener database tables
Run this once to set up the database schema
"""
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from app.db import engine, Base

# Import models directly
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
from models import PKScreenerResult, PKScreenerBacktestResult

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables():
    """Create all PKScreener tables"""
    try:
        logger.info("Creating PKScreener database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tables created successfully!")
        
        # Verify tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'pkscreener_results' in tables:
            logger.info("  ✓ pkscreener_results table created")
        if 'pkscreener_backtest_results' in tables:
            logger.info("  ✓ pkscreener_backtest_results table created")
        
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        raise


if __name__ == "__main__":
    create_tables()

