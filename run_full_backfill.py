"""
Run full backfill for all F&O stocks.
"""
import sys
import os

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data-fetch'))

from dhan_backfill_service import dhan_backfill_service

print('Starting full backfill for all F&O stocks...')
print()

# Run backfill for all stocks
dhan_backfill_service.backfill_all_stocks(
    symbols=None,  # None = all F&O stocks
    months_back=2,
    delay_seconds=1  # 1 second delay between API calls
)

print()
print('Backfill complete!')

