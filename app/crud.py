from datetime import datetime, timedelta
from typing import List, Optional
from app.db import redis_client
from app.models import Settings, AddStockRequest, WatchlistStock, AlertFilters, AlertResponse, AlertAnalysisUpdate
from app.instruments import STOCKS_LIST
from . import models
import json
import logging
import time
import os
import re

# Import MongoDB service
from app.mongo_service import (
    insert_alert,
    get_alerts as get_alerts_mongo,
    update_alert_analysis as update_alert_analysis_mongo,
    alerts_collection
)

logger = logging.getLogger(__name__)

# Import Telegram notifier
try:
    from app.telegram_notifier import send_trading_alert
    TELEGRAM_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ Telegram notifier not available")
    TELEGRAM_AVAILABLE = False

# Create a mapping from instrument_key to stock details for quick lookups
STOCKS_MAP = {stock['instrument_key']: stock for stock in STOCKS_LIST}
STOCKS_BY_SYMBOL_MAP = {stock['symbol']: stock for stock in STOCKS_LIST}

# --- In-memory fallback (updated for new structure) ---
in_memory_watchlist = {} # { "SYMBOL": {"target_price": 1, ...}}
in_memory_settings = {
    "rsi_threshold": 70,
    "telegram_alerts_enabled": True,
    "enable_pattern_alerts": True,
    "enable_rsi_alerts": False,
    "enable_super_alerts_only": False,
    "enable_double_top_bottom": True,
    "enable_triple_top_bottom": True,
    "enable_quadruple_top_bottom": True,
    "enable_pole_patterns": True,
    "enable_catapult_patterns": True,
    "dhan_access_token": None
}
in_memory_high_rsi = {} # {symbol: rsi}

# --- Watchlist Functions ---
def get_watchlist_details() -> list[WatchlistStock]:
    """
    Retrieves the full details for all stocks in the watchlist.
    """
    if not redis_client:
        return [WatchlistStock(**data) for data in in_memory_watchlist.values()]

    symbols = redis_client.smembers("watchlist:symbols")
    if not symbols:
        return []

    pipeline = redis_client.pipeline()
    for symbol in symbols:
        pipeline.hgetall(f"watchlist:details:{symbol}")
    
    results = pipeline.execute()
    
    watchlist = []
    for symbol, data in zip(symbols, results):
        if not data:
            continue
        # Manually add the symbol and instrument_key to the data dict before creating the model
        data['symbol'] = symbol
        data['instrument_key'] = data.get('instrument_key', '') # Get key from Redis, fallback to empty

        # Defensively add company_name if it's missing from old data in Redis
        if 'company_name' not in data or not data['company_name']:
            stock_info = STOCKS_BY_SYMBOL_MAP.get(symbol)
            if stock_info:
                data['company_name'] = stock_info.get('name', 'N/A')

        try:
            watchlist.append(WatchlistStock(**data))
        except Exception as e:
            logger.error(f"Could not validate watchlist stock data for {symbol}: {data}, Error: {e}")
    
    return sorted(watchlist, key=lambda s: s.added_at, reverse=True)


def add_stock_to_watchlist(stock: models.AddStockRequest):
    """
    Adds a new stock with all its details to the watchlist.
    """
    # Find the full stock info from STOCKS_LIST to get company_name etc.
    stock_info = next((s for s in STOCKS_LIST if s['instrument_key'] == stock.instrument_key), None)
    if not stock_info:
        logger.error(f"Could not find stock info for instrument key {stock.instrument_key}")
        return

    symbol = stock.symbol.upper()
    added_at = datetime.utcnow()

    # Combine data from the form (stock model) and the static instruments list
    stock_details = stock.dict(exclude_unset=True)
    stock_details.update({
        "company_name": stock_info.get("name", ""),
        "added_at": added_at.isoformat()
    })
    stock_details.pop('symbol', None) # Don't need to store symbol in the hash, it's in the key

    # Filter out any remaining None values just in case, before saving to Redis
    redis_safe_details = {k: v for k, v in stock_details.items() if v is not None}
    
    if not redis_client:
        # For in-memory, we need to reconstruct the full object
        in_memory_watchlist[symbol] = WatchlistStock(symbol=symbol, **redis_safe_details).dict()
        return

    pipeline = redis_client.pipeline()
    pipeline.sadd("watchlist:symbols", symbol)
    pipeline.hset(f"watchlist:details:{symbol}", mapping=redis_safe_details)
    pipeline.execute()


def remove_stock_from_watchlist(symbol: str):
    symbol = symbol.upper()
    if not redis_client:
        in_memory_watchlist.pop(symbol, None)
        return

    pipeline = redis_client.pipeline()
    pipeline.srem("watchlist:symbols", symbol)
    pipeline.delete(f"watchlist:details:{symbol}")
    pipeline.execute()


def delete_stock_from_watchlist(instrument_key: str):
    """
    Deletes a stock from the watchlist using its instrument key.
    Finds the symbol from the instrument key and calls remove_stock_from_watchlist.
    """
    # Find the stock info to get the symbol
    stock_info = STOCKS_MAP.get(instrument_key)
    if not stock_info:
        logger.error(f"Could not find stock info for instrument key {instrument_key}")
        return

    symbol = stock_info['symbol']
    logger.info(f"Deleting {symbol} (instrument_key: {instrument_key}) from watchlist")
    remove_stock_from_watchlist(symbol)


def add_stocks_to_watchlist_by_key(instrument_keys: list[str], tags: str):
    """
    Adds multiple stocks to the watchlist using their instrument keys.
    """
    if not instrument_keys:
        return

    added_at = datetime.utcnow().isoformat()

    if redis_client:
        pipeline = redis_client.pipeline()

    for key in instrument_keys:
        stock_data = STOCKS_MAP.get(key)
        if not stock_data:
            continue # Skip if the key is not found

        symbol = stock_data['symbol']
        
        stock_details = {
            "instrument_key": key,
            "name": stock_data['name'],
            "isin": stock_data['isin'],
            "added_at": added_at,
            "tags": tags if tags else "Untagged",
            "trade_type": "Bullish" # Default trade type
        }

        # Filter out any potential None values
        redis_safe_details = {k: v for k, v in stock_details.items() if v is not None}

        if not redis_client:
            in_memory_watchlist[symbol] = WatchlistStock(symbol=symbol, **redis_safe_details).dict()
        else:
            pipeline.sadd("watchlist:symbols", symbol)
            pipeline.hset(f"watchlist:details:{symbol}", mapping=redis_safe_details)

    if redis_client:
        pipeline.execute()


# --- Legacy function for scheduler ---
def get_watchlist() -> list[str]:
    """Returns a simple list of symbols for the background RSI checker."""
    if not redis_client:
        return list(in_memory_watchlist.keys())
    return sorted(list(redis_client.smembers("watchlist:symbols")))


# --- Helper Functions ---
def update_env_file(key: str, value: str):
    """Update or add a key-value pair in the .env file."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')

    # Read existing .env file
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
    else:
        lines = []

    # Check if key exists and update it
    key_found = False
    for i, line in enumerate(lines):
        if line.strip() and not line.strip().startswith('#'):
            if line.split('=')[0].strip() == key:
                lines[i] = f"{key}={value}\n"
                key_found = True
                break

    # If key not found, append it
    if not key_found:
        lines.append(f"{key}={value}\n")

    # Write back to .env file
    with open(env_path, 'w') as f:
        f.writelines(lines)

    # Update environment variable in current process
    os.environ[key] = value
    logger.info(f"✅ Updated {key} in .env file")

# --- Settings Functions ---
def get_settings():
    if not redis_client:
        return in_memory_settings

    settings = redis_client.hgetall("settings")

    # Get dhan_access_token from Redis, or fall back to environment variable
    dhan_token = settings.get("dhan_access_token", None)
    if not dhan_token:
        dhan_token = os.getenv("DHAN_ACCESS_TOKEN", None)

    return {
        "rsi_threshold": int(settings.get("rsi_threshold", 70)),
        "telegram_alerts_enabled": settings.get("telegram_alerts_enabled", "True") == "True",
        "enable_pattern_alerts": settings.get("enable_pattern_alerts", "True") == "True",
        "enable_rsi_alerts": settings.get("enable_rsi_alerts", "False") == "True",
        "enable_super_alerts_only": settings.get("enable_super_alerts_only", "False") == "True",
        "enable_double_top_bottom": settings.get("enable_double_top_bottom", "True") == "True",
        "enable_triple_top_bottom": settings.get("enable_triple_top_bottom", "True") == "True",
        "enable_quadruple_top_bottom": settings.get("enable_quadruple_top_bottom", "True") == "True",
        "enable_pole_patterns": settings.get("enable_pole_patterns", "True") == "True",
        "enable_catapult_patterns": settings.get("enable_catapult_patterns", "True") == "True",
        "dhan_access_token": dhan_token,
    }

def save_settings(settings: Settings):
    settings_dict = {
        "rsi_threshold": str(settings.rsi_threshold),
        "telegram_alerts_enabled": str(settings.telegram_alerts_enabled),
        "enable_pattern_alerts": str(settings.enable_pattern_alerts),
        "enable_rsi_alerts": str(settings.enable_rsi_alerts),
        "enable_super_alerts_only": str(settings.enable_super_alerts_only),
        "enable_double_top_bottom": str(settings.enable_double_top_bottom),
        "enable_triple_top_bottom": str(settings.enable_triple_top_bottom),
        "enable_quadruple_top_bottom": str(settings.enable_quadruple_top_bottom),
        "enable_pole_patterns": str(settings.enable_pole_patterns),
        "enable_catapult_patterns": str(settings.enable_catapult_patterns),
    }

    # Handle dhan_access_token separately - update .env file if provided
    if settings.dhan_access_token:
        settings_dict["dhan_access_token"] = settings.dhan_access_token
        update_env_file("DHAN_ACCESS_TOKEN", settings.dhan_access_token)

    if not redis_client:
        in_memory_settings.update(settings.dict())
        return
    redis_client.hset("settings", mapping=settings_dict)


# --- High RSI Stocks Functions ---
def get_high_rsi_stocks():
    if not redis_client:
        return {symbol: {"symbol": symbol, "rsi": rsi} for symbol, rsi in in_memory_high_rsi.items()}
    
    stocks = redis_client.hgetall("high_rsi_stocks")
    # Convert to the format expected by the frontend
    return {symbol: {"symbol": symbol, "rsi": float(rsi)} for symbol, rsi in stocks.items()}

def update_high_rsi_stocks(stocks_to_update: dict):
    """
    Updates the hash in Redis for high RSI stocks.
    `stocks_to_update` should be a dict of {symbol: rsi}.
    """
    if not redis_client:
        in_memory_high_rsi.clear()
        in_memory_high_rsi.update(stocks_to_update)
        return

    # Use a pipeline to clear and set new values efficiently
    pipeline = redis_client.pipeline()
    pipeline.delete("high_rsi_stocks")
    if stocks_to_update:
        pipeline.hset("high_rsi_stocks", mapping=stocks_to_update)
    pipeline.execute()

def get_latest_alert_for_stock(symbol: str) -> dict:
    """Retrieves the latest alert for a symbol from Redis."""
    if not redis_client:
        return None
    try:
        alert_data_str = redis_client.get(f"latest_alert:{symbol}")
        if alert_data_str:
            return json.loads(alert_data_str)
    except Exception as e:
        logger.error(f"Error fetching latest alert for {symbol} from Redis: {e}")
    return None

def get_stock_by_instrument_key(instrument_key: str) -> dict:
    """Finds a stock's details from the main STOCKS_LIST using its instrument key."""
    return STOCKS_MAP.get(instrument_key)

def get_all_stocks() -> list:
    """Get all stocks from the watchlist."""
    watchlist = get_watchlist_details()
    return [
        {
            'symbol': stock.symbol,
            'instrument_key': stock.instrument_key,
            'company_name': stock.company_name,
            'trade_type': stock.trade_type
        }
        for stock in watchlist
    ]

# --- Alert Functions ---
def save_alert(symbol: str, instrument_key: str, alert_data: dict) -> str:
    """
    Save an alert to MongoDB and send Telegram notification.

    Args:
        symbol: Trading symbol
        instrument_key: Dhan instrument key
        alert_data: Alert data from pattern detector

    Returns:
        Alert ID if saved successfully, None otherwise
    """
    start_time = time.time()

    try:
        # Extract data from alert_data
        alert_type = alert_data.get('alert_type', 'BUY')
        pattern_type = alert_data.get('pattern_type', 'unknown')
        pattern_name = alert_data.get('type', pattern_type.replace('_', ' ').title())
        signal_price = float(alert_data.get('signal_price', 0))
        trigger_reason = alert_data.get('trigger_reason', 'No reason provided')

        # Check if this is a super alert
        is_super_alert = 'SUPER' in trigger_reason.upper() or 'MATRIX SCORE' in trigger_reason.upper()

        # Extract PnF matrix score if present
        pnf_matrix_score = None
        if 'MATRIX SCORE:' in trigger_reason:
            try:
                score_part = trigger_reason.split('MATRIX SCORE:')[1].split()[0]
                pnf_matrix_score = int(score_part)
            except:
                pass

        # Extract Fibonacci level if present
        fibonacci_level = None
        if 'fibonacci' in trigger_reason.lower():
            # Extract fibonacci level from trigger reason
            fib_keywords = ['23.6%', '38.2%', '50%', '61.8%', '78.6%']
            for keyword in fib_keywords:
                if keyword in trigger_reason:
                    fibonacci_level = keyword
                    break

        # Create alert document
        alert_timestamp = datetime.utcnow()
        alert_doc = {
            "symbol": symbol,
            "instrument_key": instrument_key,
            "alert_type": alert_type,
            "pattern_type": pattern_type,
            "pattern_name": pattern_name,
            "signal_price": signal_price,
            "trigger_reason": trigger_reason,
            "is_super_alert": is_super_alert,
            "pnf_matrix_score": pnf_matrix_score,
            "fibonacci_level": fibonacci_level,
            "column_number": alert_data.get('column'),
            "volume_at_alert": alert_data.get('volume'),
            "market_conditions": alert_data.get('market_conditions'),
            "timestamp": alert_timestamp,
            "accuracy_checked": False,
            "outcome": None,
            "outcome_price": None,
            "outcome_date": None,
            "profit_loss_percent": None,
            "days_to_outcome": None,
            "notes": None
        }

        alert_id = insert_alert(alert_doc)

        db_save_time = time.time() - start_time
        logger.info(f"✅ Alert saved to MongoDB in {db_save_time*1000:.2f}ms: {symbol} - {pattern_name} @ ₹{signal_price}")

        # Send Telegram notification (non-blocking, with retry)
        if TELEGRAM_AVAILABLE:
            try:
                telegram_start = time.time()
                success = send_trading_alert(
                    symbol=symbol,
                    instrument_key=instrument_key,
                    pattern_type=pattern_type,
                    pattern_name=pattern_name,
                    alert_type=alert_type,
                    signal_price=signal_price,
                    matrix_score=pnf_matrix_score,
                    is_super_alert=is_super_alert,
                    box_size=0.0025,  # Default 0.25%
                    interval="1minute",
                    time_range="2months",
                    trigger_reason=trigger_reason,
                    timestamp=alert_timestamp.strftime("%Y-%m-%d %H:%M:%S IST")
                )
                telegram_time = time.time() - telegram_start

                if success:
                    logger.info(f"📱 Telegram alert sent in {telegram_time*1000:.2f}ms")
                else:
                    logger.warning(f"⚠️ Telegram alert failed after {telegram_time*1000:.2f}ms")

            except Exception as telegram_error:
                logger.error(f"❌ Telegram notification error: {telegram_error}")
                # Don't fail the alert save if Telegram fails

        total_time = time.time() - start_time
        logger.info(f"⏱️ Total alert processing time: {total_time*1000:.2f}ms")

        if total_time > 5.0:
            logger.warning(f"⚠️ Alert latency exceeded 5 seconds: {total_time:.2f}s")

        return alert_id

    except Exception as e:
        logger.error(f"❌ Error saving alert to MongoDB: {e}")

        # Try to send failure notification
        if TELEGRAM_AVAILABLE:
            try:
                from app.telegram_notifier import send_system_alert
                send_system_alert(
                    alert_title="Alert Generation Failed",
                    alert_message=f"Failed to save alert for {symbol} - {pattern_type}\nError: {str(e)}",
                    severity="ERROR"
                )
            except:
                pass

        return None

def get_alerts(filters: AlertFilters) -> List[AlertResponse]:
    """
    Get alerts from MongoDB with filtering.

    Args:
        filters: AlertFilters object with filtering parameters

    Returns:
        List of AlertResponse objects
    """
    try:
        # Build MongoDB query
        mongo_query = {}

        # Apply filters
        if filters.symbol:
            mongo_query["symbol"] = {"$regex": filters.symbol, "$options": "i"}

        if filters.alert_type and filters.alert_type != 'ALL':
            mongo_query["alert_type"] = filters.alert_type

        if filters.pattern_type:
            mongo_query["pattern_type"] = {"$regex": filters.pattern_type, "$options": "i"}

        if filters.is_super_alert is not None:
            mongo_query["is_super_alert"] = filters.is_super_alert

        if filters.start_date or filters.end_date:
            mongo_query["timestamp"] = {}
            if filters.start_date:
                mongo_query["timestamp"]["$gte"] = filters.start_date
            if filters.end_date:
                mongo_query["timestamp"]["$lte"] = filters.end_date

        if filters.outcome and filters.outcome != 'all':
            if filters.outcome == 'pending':
                mongo_query["outcome"] = None
            else:
                mongo_query["outcome"] = filters.outcome

        # Get alerts from MongoDB
        from pymongo import DESCENDING
        cursor = alerts_collection.find(mongo_query, {"_id": 0}).sort("timestamp", DESCENDING)

        # Apply pagination
        if filters.offset:
            cursor = cursor.skip(filters.offset)
        if filters.limit:
            cursor = cursor.limit(filters.limit)

        alerts = list(cursor)

        # Convert to response models
        return [AlertResponse(**alert) for alert in alerts]

    except Exception as e:
        logger.error(f"❌ Error fetching alerts from MongoDB: {e}")
        return []

def get_alert_statistics() -> dict:
    """
    Get alert statistics for dashboard from MongoDB.

    Returns:
        Dictionary with alert statistics
    """
    try:
        # Total alerts
        total_alerts = alerts_collection.count_documents({})

        # Super alerts
        super_alerts = alerts_collection.count_documents({"is_super_alert": True})

        # Alerts by type
        buy_alerts = alerts_collection.count_documents({"alert_type": "BUY"})
        sell_alerts = alerts_collection.count_documents({"alert_type": "SELL"})

        # Recent alerts (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_alerts = alerts_collection.count_documents({"timestamp": {"$gte": week_ago}})

        # Accuracy statistics
        analyzed_alerts = alerts_collection.count_documents({"accuracy_checked": True})
        profitable_alerts = alerts_collection.count_documents({"outcome": "profit"})

        accuracy_rate = (profitable_alerts / analyzed_alerts * 100) if analyzed_alerts > 0 else 0

        return {
            'total_alerts': total_alerts,
            'super_alerts': super_alerts,
            'buy_alerts': buy_alerts,
            'sell_alerts': sell_alerts,
            'recent_alerts': recent_alerts,
            'analyzed_alerts': analyzed_alerts,
            'profitable_alerts': profitable_alerts,
            'accuracy_rate': round(accuracy_rate, 2)
        }

    except Exception as e:
        logger.error(f"❌ Error fetching alert statistics from MongoDB: {e}")
        return {
            'total_alerts': 0,
            'super_alerts': 0,
            'buy_alerts': 0,
            'sell_alerts': 0,
            'recent_alerts': 0,
            'analyzed_alerts': 0,
            'profitable_alerts': 0,
            'accuracy_rate': 0
        }

def update_alert_analysis(analysis_update: AlertAnalysisUpdate) -> bool:
    """
    Update alert analysis data for ML purposes in MongoDB.

    Args:
        analysis_update: AlertAnalysisUpdate object with analysis data

    Returns:
        True if updated successfully, False otherwise
    """
    try:
        from bson import ObjectId

        # Find the alert
        alert = alerts_collection.find_one({"_id": ObjectId(analysis_update.alert_id)})
        if not alert:
            logger.error(f"Alert with ID {analysis_update.alert_id} not found")
            return False

        # Calculate days to outcome if outcome_date is provided
        days_to_outcome = None
        if analysis_update.outcome_date:
            days_diff = (analysis_update.outcome_date - alert["timestamp"]).days
            days_to_outcome = days_diff

        # Update analysis fields
        alerts_collection.update_one(
            {"_id": ObjectId(analysis_update.alert_id)},
            {"$set": {
                "accuracy_checked": True,
                "outcome": analysis_update.outcome,
                "outcome_price": analysis_update.outcome_price,
                "outcome_date": analysis_update.outcome_date,
                "profit_loss_percent": analysis_update.profit_loss_percent,
                "notes": analysis_update.notes,
                "days_to_outcome": days_to_outcome
            }}
        )

        logger.info(f"✅ Alert analysis updated: ID {analysis_update.alert_id} - {analysis_update.outcome}")
        return True

    except Exception as e:
        logger.error(f"❌ Error updating alert analysis in MongoDB: {e}")
        return False

def get_alerts_for_ml_analysis() -> List[AlertResponse]:
    """
    Get alerts that are ready for ML analysis (have outcome data) from MongoDB.

    Returns:
        List of AlertResponse objects with analysis data
    """
    try:
        from pymongo import DESCENDING

        alerts = list(alerts_collection.find(
            {
                "accuracy_checked": True,
                "outcome": {"$ne": None}
            },
            {"_id": 0}
        ).sort("timestamp", DESCENDING))

        return [AlertResponse(**alert) for alert in alerts]

    except Exception as e:
        logger.error(f"❌ Error fetching alerts for ML analysis from MongoDB: {e}")
        return []

def get_pattern_performance() -> dict:
    """
    Get performance statistics by pattern type from MongoDB.

    Returns:
        Dictionary with pattern performance data
    """
    try:
        # Aggregate alerts by pattern type
        pipeline = [
            {
                "$match": {
                    "accuracy_checked": True,
                    "outcome": {"$ne": None}
                }
            },
            {
                "$group": {
                    "_id": {
                        "pattern_type": "$pattern_type",
                        "pattern_name": "$pattern_name"
                    },
                    "total_alerts": {"$sum": 1},
                    "profitable": {
                        "$sum": {
                            "$cond": [{"$eq": ["$outcome", "profit"]}, 1, 0]
                        }
                    },
                    "avg_profit_loss": {"$avg": "$profit_loss_percent"},
                    "avg_days_to_outcome": {"$avg": "$days_to_outcome"}
                }
            }
        ]

        pattern_stats = list(alerts_collection.aggregate(pipeline))

        # Format results
        performance_data = []
        for stat in pattern_stats:
            total = stat['total_alerts']
            profitable = stat['profitable']
            accuracy = (profitable / total * 100) if total > 0 else 0
            performance_data.append({
                'pattern_type': stat['_id']['pattern_type'],
                'pattern_name': stat['_id']['pattern_name'],
                'total_alerts': total,
                'profitable_alerts': profitable,
                'accuracy_rate': round(accuracy, 2),
                'avg_profit_loss': round(stat['avg_profit_loss'] or 0, 2),
                'avg_days_to_outcome': round(stat['avg_days_to_outcome'] or 0, 1)
            })

        return {
            'pattern_performance': sorted(performance_data, key=lambda x: x['accuracy_rate'], reverse=True)
        }

    except Exception as e:
        logger.error(f"❌ Error fetching pattern performance from MongoDB: {e}")
        return {'pattern_performance': []}
