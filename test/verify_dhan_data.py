"""
Verify Dhan Historical Data Quality
Checks the data stored in the database after backfill.
"""

import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal
from app.models import Candle, DataSyncStatus
from sqlalchemy import func, and_


def verify_data_quality():
    """Verify the quality and completeness of backfilled data."""
    
    print("=" * 80)
    print("🔍 DHAN DATA QUALITY VERIFICATION")
    print("=" * 80)
    print()
    
    db = SessionLocal()
    
    try:
        # 1. Overall Statistics
        print("📊 OVERALL STATISTICS")
        print("-" * 80)
        
        total_candles = db.query(func.count(Candle.id)).filter(
            Candle.interval == '1minute'
        ).scalar()
        
        unique_stocks = db.query(func.count(func.distinct(Candle.instrument_key))).filter(
            Candle.interval == '1minute'
        ).scalar()
        
        print(f"   Total 1-minute candles: {total_candles:,}")
        print(f"   Unique stocks: {unique_stocks}")
        print(f"   Average candles per stock: {total_candles // unique_stocks if unique_stocks > 0 else 0:,}")
        print()
        
        # 2. Date Range
        print("📅 DATE RANGE")
        print("-" * 80)
        
        min_date = db.query(func.min(Candle.timestamp)).filter(
            Candle.interval == '1minute'
        ).scalar()
        
        max_date = db.query(func.max(Candle.timestamp)).filter(
            Candle.interval == '1minute'
        ).scalar()
        
        if min_date and max_date:
            print(f"   Earliest candle: {min_date}")
            print(f"   Latest candle: {max_date}")
            print(f"   Date range: {(max_date - min_date).days} days")
        print()
        
        # 3. Top 10 Stocks by Candle Count
        print("📈 TOP 10 STOCKS BY CANDLE COUNT")
        print("-" * 80)
        
        top_stocks = db.query(
            Candle.instrument_key,
            func.count(Candle.id).label('candle_count'),
            func.min(Candle.timestamp).label('min_date'),
            func.max(Candle.timestamp).label('max_date')
        ).filter(
            Candle.interval == '1minute'
        ).group_by(
            Candle.instrument_key
        ).order_by(
            func.count(Candle.id).desc()
        ).limit(10).all()
        
        for i, (instrument_key, count, min_dt, max_dt) in enumerate(top_stocks, 1):
            stock_symbol = instrument_key.replace('DHAN_', '')
            print(f"   {i:2d}. {stock_symbol:15s} | {count:6,} candles | {min_dt.date()} to {max_dt.date()}")
        print()
        
        # 4. Sync Status Summary
        print("✅ SYNC STATUS SUMMARY")
        print("-" * 80)
        
        sync_stats = db.query(
            DataSyncStatus.sync_status,
            func.count(DataSyncStatus.id).label('count')
        ).filter(
            DataSyncStatus.data_type == 'intraday'
        ).group_by(
            DataSyncStatus.sync_status
        ).all()
        
        for status, count in sync_stats:
            emoji = "✅" if status == "success" else "❌" if status == "failed" else "⚠️"
            print(f"   {emoji} {status.upper():10s}: {count:3d} stocks")
        print()
        
        # 5. Failed Stocks (if any)
        failed_stocks = db.query(DataSyncStatus).filter(
            and_(
                DataSyncStatus.data_type == 'intraday',
                DataSyncStatus.sync_status == 'failed'
            )
        ).all()
        
        if failed_stocks:
            print("❌ FAILED STOCKS")
            print("-" * 80)
            for sync in failed_stocks:
                print(f"   {sync.symbol:15s} | Error: {sync.error_message}")
            print()
        
        # 6. Sample Data Quality Check
        print("🔬 SAMPLE DATA QUALITY CHECK")
        print("-" * 80)
        
        # Check for any candles with zero or negative prices
        invalid_prices = db.query(func.count(Candle.id)).filter(
            and_(
                Candle.interval == '1minute',
                (Candle.close <= 0) | (Candle.open <= 0) | (Candle.high <= 0) | (Candle.low <= 0)
            )
        ).scalar()
        
        print(f"   Candles with invalid prices (<=0): {invalid_prices}")
        
        # Check for candles where high < low (data integrity issue)
        invalid_hl = db.query(func.count(Candle.id)).filter(
            and_(
                Candle.interval == '1minute',
                Candle.high < Candle.low
            )
        ).scalar()
        
        print(f"   Candles with high < low: {invalid_hl}")
        
        # Check for candles with zero volume
        zero_volume = db.query(func.count(Candle.id)).filter(
            and_(
                Candle.interval == '1minute',
                Candle.volume == 0
            )
        ).scalar()
        
        print(f"   Candles with zero volume: {zero_volume}")
        print()
        
        # 7. Sample Candles
        print("📋 SAMPLE CANDLES (Latest 5)")
        print("-" * 80)
        
        sample_candles = db.query(Candle).filter(
            Candle.interval == '1minute'
        ).order_by(
            Candle.timestamp.desc()
        ).limit(5).all()
        
        for candle in sample_candles:
            stock = candle.instrument_key.replace('DHAN_', '')
            print(f"   {stock:10s} | {candle.timestamp} | O:{candle.open:8.2f} H:{candle.high:8.2f} L:{candle.low:8.2f} C:{candle.close:8.2f} V:{candle.volume:10,}")
        print()
        
        print("=" * 80)
        print("✅ VERIFICATION COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    verify_data_quality()

