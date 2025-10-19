"""
Run Dhan Historical Data Backfill for all F&O stocks.

This script fetches 2 months of 1-minute candle data for all F&O stocks
and stores it in the PostgreSQL database.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'data-fetch'))

from dhan_backfill_service import dhan_backfill_service
from logzero import logger


def main():
    """Run the backfill for all F&O stocks."""
    
    print()
    print("=" * 80)
    print("🚀 DHAN HISTORICAL DATA BACKFILL - ALL F&O STOCKS")
    print("=" * 80)
    print()
    print("This will fetch 2 months of 1-minute candle data for all F&O stocks")
    print("and store it in the PostgreSQL database.")
    print()
    
    # Ask for confirmation
    response = input("Do you want to proceed? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("❌ Backfill cancelled.")
        return
    
    print()
    print("Starting backfill...")
    print()
    
    # Run backfill for all stocks
    dhan_backfill_service.backfill_all_stocks(
        symbols=None,  # None = all F&O stocks
        months_back=2,
        delay_seconds=1  # 1 second delay between API calls
    )
    
    print()
    print("=" * 80)
    print("✅ BACKFILL COMPLETE!")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()

