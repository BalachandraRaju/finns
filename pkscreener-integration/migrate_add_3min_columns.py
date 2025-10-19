"""
Migration script to add 3-minute interval columns to existing pkscreener_backtest_results table
Run this if you already have the table created
"""
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from app.db import engine
from sqlalchemy import text, inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """Add 3-minute interval columns"""
    try:
        logger.info("Adding 3-minute interval columns to pkscreener_backtest_results...")

        # Check if table exists
        inspector = inspect(engine)
        if 'pkscreener_backtest_results' not in inspector.get_table_names():
            logger.error("❌ Table pkscreener_backtest_results doesn't exist")
            logger.info("Run: python3 pkscreener-integration/create_tables.py")
            return

        # Check if columns already exist
        columns = [col['name'] for col in inspector.get_columns('pkscreener_backtest_results')]

        if 'price_after_3min' in columns:
            logger.info("✅ Columns already exist - no migration needed")
            return

        # Add new columns
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE pkscreener_backtest_results ADD COLUMN price_after_3min FLOAT"))
            conn.execute(text("ALTER TABLE pkscreener_backtest_results ADD COLUMN return_3min_pct FLOAT"))
            conn.commit()

            logger.info("✅ Migration complete!")
            logger.info("  ✓ Added price_after_3min column")
            logger.info("  ✓ Added return_3min_pct column")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        logger.info("\nIf table doesn't exist, run: python3 pkscreener-integration/create_tables.py")
        raise


if __name__ == "__main__":
    migrate()

