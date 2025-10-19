"""
MongoDB service for all database operations.
Replaces SQLite/SQLAlchemy with MongoDB.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pymongo import MongoClient, ASCENDING, DESCENDING
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["trading_data"]

# Collections
candles_collection = db["candles"]
ltp_data_collection = db["ltp_data"]
data_sync_status_collection = db["data_sync_status"]
alerts_collection = db["alerts"]
pkscreener_results_collection = db["pkscreener_results"]
pkscreener_backtest_results_collection = db["pkscreener_backtest_results"]

# Create indexes
def create_indexes():
    """Create all necessary indexes for optimal query performance."""
    try:
        # Candles indexes
        candles_collection.create_index([("instrument_key", ASCENDING), ("interval", ASCENDING), ("timestamp", ASCENDING)], unique=True)
        candles_collection.create_index([("instrument_key", ASCENDING)])
        candles_collection.create_index([("interval", ASCENDING)])
        candles_collection.create_index([("timestamp", ASCENDING)])
        
        # LTP data indexes
        ltp_data_collection.create_index([("symbol", ASCENDING), ("timestamp", ASCENDING)], unique=True)
        ltp_data_collection.create_index([("symbol", ASCENDING)])
        ltp_data_collection.create_index([("instrument_key", ASCENDING)])
        ltp_data_collection.create_index([("timestamp", ASCENDING)])
        
        # Data sync status indexes
        data_sync_status_collection.create_index([("symbol", ASCENDING), ("data_type", ASCENDING)], unique=True)
        data_sync_status_collection.create_index([("symbol", ASCENDING)])
        
        # Alerts indexes
        alerts_collection.create_index([("symbol", ASCENDING), ("timestamp", ASCENDING)])
        alerts_collection.create_index([("symbol", ASCENDING)])
        alerts_collection.create_index([("instrument_key", ASCENDING)])
        alerts_collection.create_index([("alert_type", ASCENDING)])
        alerts_collection.create_index([("pattern_type", ASCENDING)])
        alerts_collection.create_index([("is_super_alert", ASCENDING)])
        alerts_collection.create_index([("timestamp", ASCENDING)])
        alerts_collection.create_index([("accuracy_checked", ASCENDING), ("outcome", ASCENDING)])
        
        # PKScreener results indexes
        pkscreener_results_collection.create_index([("instrument_key", ASCENDING), ("scan_timestamp", ASCENDING)])
        pkscreener_results_collection.create_index([("scanner_id", ASCENDING)])
        pkscreener_results_collection.create_index([("symbol", ASCENDING)])
        
        # PKScreener backtest results indexes
        pkscreener_backtest_results_collection.create_index([("scanner_id", ASCENDING), ("backtest_date", ASCENDING)])
        pkscreener_backtest_results_collection.create_index([("instrument_key", ASCENDING)])
        pkscreener_backtest_results_collection.create_index([("symbol", ASCENDING)])
        
        logger.info("✅ MongoDB indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")

# Initialize indexes on module import
create_indexes()

# --- Candles Operations ---
def insert_candle(candle_data: Dict[str, Any]) -> bool:
    """Insert a single candle into MongoDB."""
    try:
        candles_collection.insert_one(candle_data)
        return True
    except Exception as e:
        if "duplicate key error" not in str(e).lower():
            logger.error(f"Error inserting candle: {e}")
        return False

def insert_candles_bulk(candles: List[Dict[str, Any]]) -> int:
    """Insert multiple candles into MongoDB."""
    if not candles:
        return 0
    try:
        result = candles_collection.insert_many(candles, ordered=False)
        return len(result.inserted_ids)
    except Exception as e:
        # Count successful inserts even if some fail due to duplicates
        if "duplicate key error" in str(e).lower():
            return len([c for c in candles]) - len(getattr(e, 'details', {}).get('writeErrors', []))
        logger.error(f"Error inserting candles: {e}")
        return 0

def get_candles(instrument_key: str, interval: str, start_time: datetime = None, end_time: datetime = None, limit: int = None) -> List[Dict]:
    """Get candles for a specific instrument and interval."""
    try:
        query = {"instrument_key": instrument_key, "interval": interval}
        if start_time or end_time:
            query["timestamp"] = {}
            if start_time:
                query["timestamp"]["$gte"] = start_time
            if end_time:
                query["timestamp"]["$lte"] = end_time
        
        cursor = candles_collection.find(query, {"_id": 0}).sort("timestamp", ASCENDING)
        if limit:
            cursor = cursor.limit(limit)
        
        return list(cursor)
    except Exception as e:
        logger.error(f"Error getting candles: {e}")
        return []

def delete_candles(instrument_key: str, interval: str) -> int:
    """Delete all candles for a specific instrument and interval."""
    try:
        result = candles_collection.delete_many({"instrument_key": instrument_key, "interval": interval})
        return result.deleted_count
    except Exception as e:
        logger.error(f"Error deleting candles: {e}")
        return 0

# --- LTP Data Operations ---
def insert_ltp_data(ltp_data: Dict[str, Any]) -> bool:
    """Insert LTP data into MongoDB."""
    try:
        ltp_data_collection.insert_one(ltp_data)
        return True
    except Exception as e:
        if "duplicate key error" not in str(e).lower():
            logger.error(f"Error inserting LTP data: {e}")
        return False

def get_latest_ltp(symbol: str) -> Optional[Dict]:
    """Get the latest LTP data for a symbol."""
    try:
        return ltp_data_collection.find_one({"symbol": symbol}, {"_id": 0}, sort=[("timestamp", DESCENDING)])
    except Exception as e:
        logger.error(f"Error getting latest LTP: {e}")
        return None

# --- Data Sync Status Operations ---
def upsert_sync_status(symbol: str, data_type: str, sync_status: str, records_synced: int = 0, error_message: str = None) -> bool:
    """Update or insert sync status."""
    try:
        data_sync_status_collection.update_one(
            {"symbol": symbol, "data_type": data_type},
            {"$set": {
                "last_sync": datetime.utcnow(),
                "sync_status": sync_status,
                "records_synced": records_synced,
                "error_message": error_message
            }},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Error upserting sync status: {e}")
        return False

def get_sync_status(symbol: str, data_type: str) -> Optional[Dict]:
    """Get sync status for a symbol and data type."""
    try:
        return data_sync_status_collection.find_one({"symbol": symbol, "data_type": data_type}, {"_id": 0})
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        return None

# --- Alerts Operations ---
def insert_alert(alert_data: Dict[str, Any]) -> Optional[str]:
    """Insert an alert into MongoDB."""
    try:
        result = alerts_collection.insert_one(alert_data)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error inserting alert: {e}")
        return None

def get_alerts(filters: Dict[str, Any] = None, limit: int = 100, offset: int = 0) -> List[Dict]:
    """Get alerts with optional filters."""
    try:
        query = filters or {}
        return list(alerts_collection.find(query, {"_id": 0}).sort("timestamp", DESCENDING).skip(offset).limit(limit))
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return []

def get_latest_alert_for_stock(symbol: str) -> Optional[Dict]:
    """Get the latest alert for a specific stock."""
    try:
        return alerts_collection.find_one({"symbol": symbol}, {"_id": 0}, sort=[("timestamp", DESCENDING)])
    except Exception as e:
        logger.error(f"Error getting latest alert: {e}")
        return None

def update_alert_analysis(alert_id: str, outcome: str, outcome_price: float, profit_loss_percent: float, days_to_outcome: int) -> bool:
    """Update alert with analysis data."""
    try:
        from bson import ObjectId
        alerts_collection.update_one(
            {"_id": ObjectId(alert_id)},
            {"$set": {
                "accuracy_checked": True,
                "outcome": outcome,
                "outcome_price": outcome_price,
                "outcome_date": datetime.utcnow(),
                "profit_loss_percent": profit_loss_percent,
                "days_to_outcome": days_to_outcome
            }}
        )
        return True
    except Exception as e:
        logger.error(f"Error updating alert analysis: {e}")
        return False

# --- PKScreener Results Operations ---
def insert_pkscreener_result(result_data: Dict[str, Any]) -> Optional[str]:
    """Insert a PKScreener result into MongoDB."""
    try:
        result = pkscreener_results_collection.insert_one(result_data)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error inserting PKScreener result: {e}")
        return None

def get_pkscreener_results(scanner_id: int = None, symbol: str = None, limit: int = 100) -> List[Dict]:
    """Get PKScreener results with optional filters."""
    try:
        query = {}
        if scanner_id:
            query["scanner_id"] = scanner_id
        if symbol:
            query["symbol"] = symbol
        return list(pkscreener_results_collection.find(query, {"_id": 0}).sort("scan_timestamp", DESCENDING).limit(limit))
    except Exception as e:
        logger.error(f"Error getting PKScreener results: {e}")
        return []

# --- PKScreener Backtest Results Operations ---
def insert_backtest_result(result_data: Dict[str, Any]) -> Optional[str]:
    """Insert a backtest result into MongoDB."""
    try:
        result = pkscreener_backtest_results_collection.insert_one(result_data)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error inserting backtest result: {e}")
        return None

def insert_backtest_results_bulk(results: List[Dict[str, Any]]) -> int:
    """Insert multiple backtest results into MongoDB."""
    if not results:
        return 0
    try:
        result = pkscreener_backtest_results_collection.insert_many(results)
        return len(result.inserted_ids)
    except Exception as e:
        logger.error(f"Error inserting backtest results: {e}")
        return 0

def get_backtest_results(scanner_id: int = None, symbol: str = None, start_date: datetime = None, end_date: datetime = None, limit: int = 1000) -> List[Dict]:
    """Get backtest results with optional filters."""
    try:
        query = {}
        if scanner_id:
            query["scanner_id"] = scanner_id
        if symbol:
            query["symbol"] = symbol
        if start_date or end_date:
            query["backtest_date"] = {}
            if start_date:
                query["backtest_date"]["$gte"] = start_date
            if end_date:
                query["backtest_date"]["$lte"] = end_date
        
        return list(pkscreener_backtest_results_collection.find(query, {"_id": 0}).sort("backtest_date", DESCENDING).limit(limit))
    except Exception as e:
        logger.error(f"Error getting backtest results: {e}")
        return []

