"""
Migration script to move all data from SQLite to MongoDB.
Run this script once to migrate existing data.
"""
import sqlite3
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from app.mongo_service import (
    insert_candles_bulk,
    insert_ltp_data,
    upsert_sync_status,
    insert_alert,
    insert_pkscreener_result,
    insert_backtest_result
)

def migrate_candles():
    """Migrate candles table from SQLite to MongoDB."""
    logger.info("📊 Migrating candles...")
    try:
        conn = sqlite3.connect('historical_data.db')
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM candles")
        total = cursor.fetchone()[0]
        logger.info(f"Found {total} candles to migrate")
        
        # Fetch in batches
        batch_size = 10000
        offset = 0
        migrated = 0
        
        while offset < total:
            cursor.execute(f"""
                SELECT instrument_key, interval, timestamp, open, high, low, close, volume, oi
                FROM candles
                LIMIT {batch_size} OFFSET {offset}
            """)
            
            rows = cursor.fetchall()
            if not rows:
                break
            
            candles = []
            for row in rows:
                candles.append({
                    "instrument_key": row[0],
                    "interval": row[1],
                    "timestamp": datetime.fromisoformat(row[2]) if isinstance(row[2], str) else row[2],
                    "open": float(row[3]),
                    "high": float(row[4]),
                    "low": float(row[5]),
                    "close": float(row[6]),
                    "volume": int(row[7]),
                    "oi": int(row[8]) if row[8] else 0
                })
            
            inserted = insert_candles_bulk(candles)
            migrated += inserted
            offset += batch_size
            logger.info(f"Migrated {migrated}/{total} candles...")
        
        conn.close()
        logger.info(f"✅ Migrated {migrated} candles successfully")
        return migrated
        
    except Exception as e:
        logger.error(f"❌ Error migrating candles: {e}")
        return 0

def migrate_ltp_data():
    """Migrate ltp_data table from SQLite to MongoDB."""
    logger.info("📊 Migrating LTP data...")
    try:
        conn = sqlite3.connect('historical_data.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM ltp_data")
        total = cursor.fetchone()[0]
        logger.info(f"Found {total} LTP records to migrate")
        
        cursor.execute("""
            SELECT symbol, instrument_key, ltp, timestamp, volume, change, change_percent
            FROM ltp_data
        """)
        
        migrated = 0
        for row in cursor.fetchall():
            ltp_data = {
                "symbol": row[0],
                "instrument_key": row[1],
                "ltp": float(row[2]),
                "timestamp": datetime.fromisoformat(row[3]) if isinstance(row[3], str) else row[3],
                "volume": int(row[4]) if row[4] else None,
                "change": float(row[5]) if row[5] else None,
                "change_percent": float(row[6]) if row[6] else None
            }
            if insert_ltp_data(ltp_data):
                migrated += 1
        
        conn.close()
        logger.info(f"✅ Migrated {migrated} LTP records successfully")
        return migrated
        
    except Exception as e:
        logger.error(f"❌ Error migrating LTP data: {e}")
        return 0

def migrate_data_sync_status():
    """Migrate data_sync_status table from SQLite to MongoDB."""
    logger.info("📊 Migrating data sync status...")
    try:
        conn = sqlite3.connect('historical_data.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM data_sync_status")
        total = cursor.fetchone()[0]
        logger.info(f"Found {total} sync status records to migrate")
        
        cursor.execute("""
            SELECT symbol, data_type, last_sync, sync_status, error_message, records_synced
            FROM data_sync_status
        """)
        
        migrated = 0
        for row in cursor.fetchall():
            if upsert_sync_status(
                symbol=row[0],
                data_type=row[1],
                sync_status=row[3],
                records_synced=int(row[5]) if row[5] else 0,
                error_message=row[4]
            ):
                migrated += 1
        
        conn.close()
        logger.info(f"✅ Migrated {migrated} sync status records successfully")
        return migrated
        
    except Exception as e:
        logger.error(f"❌ Error migrating sync status: {e}")
        return 0

def migrate_alerts():
    """Migrate alerts table from SQLite to MongoDB."""
    logger.info("📊 Migrating alerts...")
    try:
        conn = sqlite3.connect('historical_data.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM alerts")
        total = cursor.fetchone()[0]
        logger.info(f"Found {total} alerts to migrate")
        
        cursor.execute("""
            SELECT symbol, instrument_key, alert_type, pattern_type, pattern_name,
                   signal_price, trigger_reason, is_super_alert, pnf_matrix_score,
                   fibonacci_level, column_number, timestamp, accuracy_checked,
                   outcome, outcome_price, outcome_date, profit_loss_percent,
                   days_to_outcome, market_conditions, volume_at_alert, notes
            FROM alerts
        """)
        
        migrated = 0
        for row in cursor.fetchall():
            alert_data = {
                "symbol": row[0],
                "instrument_key": row[1],
                "alert_type": row[2],
                "pattern_type": row[3],
                "pattern_name": row[4],
                "signal_price": float(row[5]),
                "trigger_reason": row[6],
                "is_super_alert": bool(row[7]),
                "pnf_matrix_score": int(row[8]) if row[8] else None,
                "fibonacci_level": row[9],
                "column_number": int(row[10]) if row[10] else None,
                "timestamp": datetime.fromisoformat(row[11]) if isinstance(row[11], str) else row[11],
                "accuracy_checked": bool(row[12]),
                "outcome": row[13],
                "outcome_price": float(row[14]) if row[14] else None,
                "outcome_date": datetime.fromisoformat(row[15]) if row[15] and isinstance(row[15], str) else row[15],
                "profit_loss_percent": float(row[16]) if row[16] else None,
                "days_to_outcome": int(row[17]) if row[17] else None,
                "market_conditions": row[18],
                "volume_at_alert": int(row[19]) if row[19] else None,
                "notes": row[20]
            }
            if insert_alert(alert_data):
                migrated += 1
        
        conn.close()
        logger.info(f"✅ Migrated {migrated} alerts successfully")
        return migrated
        
    except Exception as e:
        logger.error(f"❌ Error migrating alerts: {e}")
        return 0

def migrate_pkscreener_results():
    """Migrate pkscreener_results table from SQLite to MongoDB."""
    logger.info("📊 Migrating PKScreener results...")
    try:
        conn = sqlite3.connect('historical_data.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM pkscreener_results")
        total = cursor.fetchone()[0]
        logger.info(f"Found {total} PKScreener results to migrate")
        
        cursor.execute("""
            SELECT scanner_id, scanner_name, instrument_key, symbol, scan_timestamp,
                   trigger_price, volume, volume_ratio, atr_value, rsi_value,
                   rsi_intraday, momentum_score, vcp_score, additional_metrics,
                   is_active, created_at
            FROM pkscreener_results
        """)
        
        migrated = 0
        for row in cursor.fetchall():
            result_data = {
                "scanner_id": int(row[0]),
                "scanner_name": row[1],
                "instrument_key": row[2],
                "symbol": row[3],
                "scan_timestamp": datetime.fromisoformat(row[4]) if isinstance(row[4], str) else row[4],
                "trigger_price": float(row[5]),
                "volume": int(row[6]) if row[6] else None,
                "volume_ratio": float(row[7]) if row[7] else None,
                "atr_value": float(row[8]) if row[8] else None,
                "rsi_value": float(row[9]) if row[9] else None,
                "rsi_intraday": float(row[10]) if row[10] else None,
                "momentum_score": float(row[11]) if row[11] else None,
                "vcp_score": float(row[12]) if row[12] else None,
                "additional_metrics": row[13],
                "is_active": bool(row[14]),
                "created_at": datetime.fromisoformat(row[15]) if row[15] and isinstance(row[15], str) else row[15]
            }
            if insert_pkscreener_result(result_data):
                migrated += 1
        
        conn.close()
        logger.info(f"✅ Migrated {migrated} PKScreener results successfully")
        return migrated
        
    except Exception as e:
        logger.error(f"❌ Error migrating PKScreener results: {e}")
        return 0

def migrate_pkscreener_backtest_results():
    """Migrate pkscreener_backtest_results table from SQLite to MongoDB."""
    logger.info("📊 Migrating PKScreener backtest results...")
    try:
        conn = sqlite3.connect('historical_data.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM pkscreener_backtest_results")
        total = cursor.fetchone()[0]
        logger.info(f"Found {total} backtest results to migrate")
        
        # Get column names
        cursor.execute("PRAGMA table_info(pkscreener_backtest_results)")
        columns = [col[1] for col in cursor.fetchall()]
        
        cursor.execute(f"SELECT * FROM pkscreener_backtest_results")
        
        migrated = 0
        for row in cursor.fetchall():
            result_data = {}
            for i, col in enumerate(columns):
                if col == 'id':
                    continue  # Skip SQLite ID
                value = row[i]
                # Convert datetime strings
                if col in ['backtest_date', 'trigger_time', 'max_profit_time', 'max_loss_time', 'created_at'] and value:
                    value = datetime.fromisoformat(value) if isinstance(value, str) else value
                result_data[col] = value
            
            if insert_backtest_result(result_data):
                migrated += 1
        
        conn.close()
        logger.info(f"✅ Migrated {migrated} backtest results successfully")
        return migrated
        
    except Exception as e:
        logger.error(f"❌ Error migrating backtest results: {e}")
        return 0

def main():
    """Run all migrations."""
    logger.info("=" * 80)
    logger.info("🚀 Starting SQLite to MongoDB migration")
    logger.info("=" * 80)
    
    total_migrated = 0
    
    # Migrate each table
    total_migrated += migrate_candles()
    total_migrated += migrate_ltp_data()
    total_migrated += migrate_data_sync_status()
    total_migrated += migrate_alerts()
    total_migrated += migrate_pkscreener_results()
    total_migrated += migrate_pkscreener_backtest_results()
    
    logger.info("=" * 80)
    logger.info(f"✅ Migration complete! Total records migrated: {total_migrated}")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()

