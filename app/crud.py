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
    "enable_turtle_patterns": True,
    "enable_aft_patterns": True,
    "enable_tweezer_patterns": True,
    "enable_abc_patterns": True,
    "enable_ziddi_patterns": True,
    "enable_fibonacci_bullish_scanner": True,
    "enable_fibonacci_bearish_scanner": True,
    "fibonacci_telegram_alerts": False,
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
        "enable_turtle_patterns": settings.get("enable_turtle_patterns", "True") == "True",
        "enable_aft_patterns": settings.get("enable_aft_patterns", "True") == "True",
        "enable_tweezer_patterns": settings.get("enable_tweezer_patterns", "True") == "True",
        "enable_abc_patterns": settings.get("enable_abc_patterns", "True") == "True",
        "enable_ziddi_patterns": settings.get("enable_ziddi_patterns", "True") == "True",
        "enable_fibonacci_bullish_scanner": settings.get("enable_fibonacci_bullish_scanner", "True") == "True",
        "enable_fibonacci_bearish_scanner": settings.get("enable_fibonacci_bearish_scanner", "True") == "True",
        "fibonacci_telegram_alerts": settings.get("fibonacci_telegram_alerts", "False") == "True",
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
        "enable_turtle_patterns": str(settings.enable_turtle_patterns),
        "enable_aft_patterns": str(settings.enable_aft_patterns),
        "enable_tweezer_patterns": str(settings.enable_tweezer_patterns),
        "enable_abc_patterns": str(settings.enable_abc_patterns),
        "enable_ziddi_patterns": str(settings.enable_ziddi_patterns),
        "enable_fibonacci_bullish_scanner": str(settings.enable_fibonacci_bullish_scanner),
        "enable_fibonacci_bearish_scanner": str(settings.enable_fibonacci_bearish_scanner),
        "fibonacci_telegram_alerts": str(settings.fibonacci_telegram_alerts),
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
def save_alert(symbol: str, instrument_key: str, alert_data: dict, send_telegram: bool = True) -> str:
    """
    Save an alert to MongoDB and optionally send Telegram notification.

    Args:
        symbol: Trading symbol
        instrument_key: Dhan instrument key
        alert_data: Alert data from pattern detector
        send_telegram: Whether to send Telegram notification (default: True)
                      Set to False when called from parallel scheduler to avoid duplicates

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

        # Get environment from alert_data or detect from environment variable
        environment = alert_data.get('environment')
        if not environment:
            import os
            environment = "LOCAL"  # Default
            if os.getenv("ENVIRONMENT") == "PRODUCTION":
                environment = "PRODUCTION"
            elif os.getenv("ENVIRONMENT") == "TEST":
                environment = "TEST"

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
            "is_super_alert": alert_data.get('is_super_alert', is_super_alert),
            "pnf_matrix_score": alert_data.get('pnf_matrix_score') or pnf_matrix_score,
            "fibonacci_level": alert_data.get('fibonacci_level') or fibonacci_level,
            "column_number": alert_data.get('column'),
            "volume_at_alert": alert_data.get('volume'),
            "market_conditions": alert_data.get('market_conditions'),
            "environment": environment,
            "timestamp": alert_timestamp,
            "accuracy_checked": False,
            "outcome": None,
            "outcome_price": None,
            "outcome_date": None,
            "profit_loss_percent": None,
            "days_to_outcome": None,
            "validation_status": "PENDING",
            "validated_by": None,
            "validation_date": None,
            "notes": None
        }

        alert_id = insert_alert(alert_doc)

        db_save_time = time.time() - start_time
        logger.info(f"✅ Alert saved to MongoDB in {db_save_time*1000:.2f}ms: {symbol} - {pattern_name} @ ₹{signal_price}")

        # Send Telegram notification (non-blocking, with retry)
        # Only send if send_telegram=True (to avoid duplicates from parallel scheduler)
        if send_telegram and TELEGRAM_AVAILABLE:
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
        elif not send_telegram:
            logger.debug(f"📱 Telegram notification skipped (handled by scheduler)")

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

# --- Pattern Validation Functions ---

def get_alerts_with_filters(filters: models.AlertFilters) -> List[models.AlertResponse]:
    """Get alerts with enhanced filtering for validation dashboard."""
    try:
        # Use the alerts collection from mongo_service
        collection = alerts_collection

        # Build query
        query = {}

        if filters.symbol:
            query["symbol"] = {"$regex": filters.symbol, "$options": "i"}
        if filters.alert_type and filters.alert_type != "ALL":
            query["alert_type"] = filters.alert_type
        if filters.pattern_type:
            query["pattern_type"] = {"$regex": filters.pattern_type, "$options": "i"}
        if filters.is_super_alert is not None:
            query["is_super_alert"] = filters.is_super_alert
        if filters.outcome and filters.outcome != "ALL":
            query["outcome"] = filters.outcome
        if filters.validation_status and filters.validation_status != "ALL":
            query["validation_status"] = filters.validation_status
        if filters.environment and filters.environment != "ALL":
            query["environment"] = filters.environment
        if filters.fibonacci_level:
            query["fibonacci_level"] = filters.fibonacci_level

        # Date range filter
        if filters.start_date or filters.end_date:
            date_query = {}
            if filters.start_date:
                if isinstance(filters.start_date, str):
                    date_query["$gte"] = datetime.fromisoformat(filters.start_date.replace('Z', '+00:00'))
                else:
                    date_query["$gte"] = filters.start_date
            if filters.end_date:
                if isinstance(filters.end_date, str):
                    date_query["$lte"] = datetime.fromisoformat(filters.end_date.replace('Z', '+00:00'))
                else:
                    date_query["$lte"] = filters.end_date
            query["timestamp"] = date_query

        # Execute query with pagination
        cursor = collection.find(query).sort("timestamp", -1).skip(filters.offset).limit(filters.limit)

        alerts = []
        for doc in cursor:
            try:
                # Convert MongoDB document to dictionary
                doc['id'] = str(doc['_id'])
                del doc['_id']

                # Ensure all required fields have default values for backward compatibility
                doc.setdefault('environment', 'LOCAL')
                doc.setdefault('validation_status', 'PENDING')
                doc.setdefault('validated_by', None)
                doc.setdefault('validation_date', None)
                doc.setdefault('fibonacci_level', None)
                doc.setdefault('pnf_matrix_score', None)
                doc.setdefault('column_number', None)
                doc.setdefault('accuracy_checked', False)
                doc.setdefault('outcome', None)
                doc.setdefault('outcome_price', None)
                doc.setdefault('outcome_date', None)
                doc.setdefault('profit_loss_percent', None)
                doc.setdefault('days_to_outcome', None)
                doc.setdefault('market_conditions', None)
                doc.setdefault('volume_at_alert', None)
                doc.setdefault('notes', None)

                # Ensure required fields exist
                doc.setdefault('symbol', 'UNKNOWN')
                doc.setdefault('alert_type', 'BUY')
                doc.setdefault('pattern_type', 'unknown')
                doc.setdefault('pattern_name', doc.get('pattern_type', 'unknown'))
                doc.setdefault('signal_price', 0.0)
                doc.setdefault('trigger_reason', 'No reason provided')
                doc.setdefault('is_super_alert', False)
                doc.setdefault('timestamp', datetime.utcnow())

                # Add the document as dictionary (no need for Pydantic model conversion)
                alerts.append(doc)

            except Exception as e:
                logger.error(f"❌ Error converting alert document: {e}")
                logger.error(f"Document: {doc}")
                continue

        return alerts

    except Exception as e:
        logger.error(f"❌ Error fetching alerts with filters: {e}")
        return []

def get_alerts_count_with_filters(filters: models.AlertFilters) -> int:
    """Get total count of alerts matching filters."""
    try:
        # Use the alerts collection from mongo_service
        collection = alerts_collection

        # Build same query as get_alerts_with_filters
        query = {}

        if filters.symbol:
            query["symbol"] = {"$regex": filters.symbol, "$options": "i"}
        if filters.alert_type and filters.alert_type != "ALL":
            query["alert_type"] = filters.alert_type
        if filters.pattern_type:
            query["pattern_type"] = {"$regex": filters.pattern_type, "$options": "i"}
        if filters.is_super_alert is not None:
            query["is_super_alert"] = filters.is_super_alert
        if filters.outcome and filters.outcome != "ALL":
            query["outcome"] = filters.outcome
        if filters.validation_status and filters.validation_status != "ALL":
            query["validation_status"] = filters.validation_status
        if filters.environment and filters.environment != "ALL":
            query["environment"] = filters.environment
        if filters.fibonacci_level:
            query["fibonacci_level"] = filters.fibonacci_level

        # Date range filter
        if filters.start_date or filters.end_date:
            date_query = {}
            if filters.start_date:
                if isinstance(filters.start_date, str):
                    date_query["$gte"] = datetime.fromisoformat(filters.start_date.replace('Z', '+00:00'))
                else:
                    date_query["$gte"] = filters.start_date
            if filters.end_date:
                if isinstance(filters.end_date, str):
                    date_query["$lte"] = datetime.fromisoformat(filters.end_date.replace('Z', '+00:00'))
                else:
                    date_query["$lte"] = filters.end_date
            query["timestamp"] = date_query

        return collection.count_documents(query)

    except Exception as e:
        logger.error(f"❌ Error counting alerts with filters: {e}")
        return 0

def update_alert_validation(alert_id: str, validation_status: str, notes: str = None, validated_by: str = None) -> bool:
    """Update alert validation status."""
    try:
        # Use the alerts collection from mongo_service
        collection = alerts_collection

        update_data = {
            "validation_status": validation_status,
            "validation_date": datetime.utcnow()
        }

        if notes:
            update_data["notes"] = notes
        if validated_by:
            update_data["validated_by"] = validated_by

        result = collection.update_one(
            {"_id": ObjectId(alert_id)},
            {"$set": update_data}
        )

        return result.modified_count > 0

    except Exception as e:
        logger.error(f"❌ Error updating alert validation: {e}")
        return False

def get_pattern_analytics(start_date: str = None, end_date: str = None, environment: str = None) -> List[dict]:
    """Get pattern performance analytics with Redis caching."""
    try:
        # Create cache key
        cache_key = f"pattern_analytics:{start_date or 'all'}:{end_date or 'all'}:{environment or 'all'}"

        # Try to get from cache first
        if redis_client:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                import json
                logger.info(f"📊 Returning cached pattern analytics for {cache_key}")
                return json.loads(cached_result)

        # Use the alerts collection from mongo_service
        collection = alerts_collection

        # Build match query
        match_query = {}

        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if end_date:
                date_query["$lte"] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            match_query["timestamp"] = date_query

        if environment and environment != "ALL":
            match_query["environment"] = environment

        # Aggregation pipeline for pattern analytics
        pipeline = [
            {"$match": match_query},
            {
                "$group": {
                    "_id": {
                        "pattern_type": "$pattern_type",
                        "environment": "$environment"
                    },
                    "total_alerts": {"$sum": 1},
                    "success_count": {
                        "$sum": {"$cond": [{"$eq": ["$outcome", "SUCCESS"]}, 1, 0]}
                    },
                    "failure_count": {
                        "$sum": {"$cond": [{"$eq": ["$outcome", "FAILURE"]}, 1, 0]}
                    },
                    "avg_profit_loss": {"$avg": "$profit_loss_percent"},
                    "avg_days_to_outcome": {"$avg": "$days_to_outcome"},
                    "fibonacci_levels": {"$push": "$fibonacci_level"}
                }
            },
            {
                "$project": {
                    "pattern_type": "$_id.pattern_type",
                    "environment": "$_id.environment",
                    "total_alerts": 1,
                    "success_count": 1,
                    "failure_count": 1,
                    "success_rate": {
                        "$cond": [
                            {"$gt": [{"$add": ["$success_count", "$failure_count"]}, 0]},
                            {"$multiply": [
                                {"$divide": ["$success_count", {"$add": ["$success_count", "$failure_count"]}]},
                                100
                            ]},
                            0
                        ]
                    },
                    "avg_profit_loss": {"$ifNull": ["$avg_profit_loss", 0]},
                    "avg_days_to_outcome": {"$ifNull": ["$avg_days_to_outcome", 0]},
                    "fibonacci_levels": 1
                }
            },
            {"$sort": {"success_rate": -1}}
        ]

        analytics = list(collection.aggregate(pipeline))

        # Process fibonacci level performance
        for analytic in analytics:
            fib_levels = [level for level in analytic.get('fibonacci_levels', []) if level]
            fib_performance = {}
            for level in set(fib_levels):
                count = fib_levels.count(level)
                fib_performance[level] = {
                    "count": count,
                    "percentage": (count / len(fib_levels) * 100) if fib_levels else 0
                }
            analytic['fibonacci_level_performance'] = fib_performance
            del analytic['fibonacci_levels']

        # Cache the result for 5 minutes
        if redis_client and analytics:
            import json
            redis_client.setex(cache_key, 300, json.dumps(analytics))  # 5 minutes cache
            logger.info(f"📊 Cached pattern analytics for {cache_key}")

        return analytics

    except Exception as e:
        logger.error(f"❌ Error fetching pattern analytics: {e}")
        return []

def get_daily_pattern_summary(date: str) -> dict:
    """Get daily pattern summary for specified date with Redis caching."""
    try:
        # Create cache key
        cache_key = f"daily_summary:{date}"

        # Try to get from cache first
        if redis_client:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                import json
                logger.info(f"📊 Returning cached daily summary for {date}")
                return json.loads(cached_result)

        # Use the alerts collection from mongo_service
        collection = alerts_collection

        # Parse date and create date range for the day
        target_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Aggregation pipeline for daily summary
        pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": start_of_day, "$lte": end_of_day}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_alerts": {"$sum": 1},
                    "buy_alerts": {
                        "$sum": {"$cond": [{"$eq": ["$alert_type", "BUY"]}, 1, 0]}
                    },
                    "sell_alerts": {
                        "$sum": {"$cond": [{"$eq": ["$alert_type", "SELL"]}, 1, 0]}
                    },
                    "super_alerts": {
                        "$sum": {"$cond": ["$is_super_alert", 1, 0]}
                    },
                    "patterns": {"$push": "$pattern_type"},
                    "environments": {"$push": "$environment"},
                    "validations": {"$push": "$validation_status"},
                    "outcomes": {"$push": "$outcome"}
                }
            }
        ]

        result = list(collection.aggregate(pipeline))

        if not result:
            return {
                "date": date,
                "total_alerts": 0,
                "buy_alerts": 0,
                "sell_alerts": 0,
                "super_alerts": 0,
                "pattern_breakdown": {},
                "environment_breakdown": {},
                "validation_breakdown": {},
                "outcome_breakdown": {}
            }

        data = result[0]

        # Calculate breakdowns
        pattern_breakdown = {}
        for pattern in data.get('patterns', []):
            pattern_breakdown[pattern] = pattern_breakdown.get(pattern, 0) + 1

        environment_breakdown = {}
        for env in data.get('environments', []):
            environment_breakdown[env] = environment_breakdown.get(env, 0) + 1

        validation_breakdown = {}
        for validation in data.get('validations', []):
            if validation:
                validation_breakdown[validation] = validation_breakdown.get(validation, 0) + 1

        outcome_breakdown = {}
        for outcome in data.get('outcomes', []):
            if outcome:
                outcome_breakdown[outcome] = outcome_breakdown.get(outcome, 0) + 1

        return {
            "date": date,
            "total_alerts": data.get('total_alerts', 0),
            "buy_alerts": data.get('buy_alerts', 0),
            "sell_alerts": data.get('sell_alerts', 0),
            "super_alerts": data.get('super_alerts', 0),
            "pattern_breakdown": pattern_breakdown,
            "environment_breakdown": environment_breakdown,
            "validation_breakdown": validation_breakdown,
            "outcome_breakdown": outcome_breakdown
        }

        # Cache the result for 1 hour (daily data doesn't change frequently)
        if redis_client:
            import json
            redis_client.setex(cache_key, 3600, json.dumps(summary))  # 1 hour cache
            logger.info(f"📊 Cached daily summary for {date}")

        return summary

    except Exception as e:
        logger.error(f"❌ Error fetching daily summary: {e}")
        return {
            "date": date,
            "total_alerts": 0,
            "buy_alerts": 0,
            "sell_alerts": 0,
            "super_alerts": 0,
            "pattern_breakdown": {},
            "environment_breakdown": {},
            "validation_breakdown": {},
            "outcome_breakdown": {}
        }

def export_alerts_to_csv(filters: models.AlertFilters) -> str:
    """Export alerts to CSV format."""
    try:
        import csv
        import io

        alerts = get_alerts_with_filters(filters)

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Symbol', 'Alert Type', 'Pattern Type', 'Pattern Name', 'Signal Price',
            'Timestamp', 'Environment', 'Is Super Alert', 'Fibonacci Level',
            'Validation Status', 'Outcome', 'Profit/Loss %', 'Days to Outcome',
            'Validated By', 'Notes', 'Trigger Reason'
        ])

        # Write data
        for alert in alerts:
            writer.writerow([
                alert.symbol,
                alert.alert_type,
                alert.pattern_type,
                alert.pattern_name,
                alert.signal_price,
                alert.timestamp.isoformat() if alert.timestamp else '',
                alert.environment,
                'Yes' if alert.is_super_alert else 'No',
                alert.fibonacci_level or '',
                alert.validation_status or '',
                alert.outcome or '',
                alert.profit_loss_percent or '',
                alert.days_to_outcome or '',
                alert.validated_by or '',
                alert.notes or '',
                alert.trigger_reason
            ])

        return output.getvalue()

    except Exception as e:
        logger.error(f"❌ Error exporting alerts to CSV: {e}")
        return ""

def ensure_pattern_validation_indexes():
    """Ensure proper database indexes for pattern validation queries."""
    try:
        # Use the alerts collection from mongo_service
        collection = alerts_collection

        # Create indexes for common query patterns
        indexes_to_create = [
            # Single field indexes
            ("timestamp", -1),  # Descending for recent alerts first
            ("symbol", 1),
            ("alert_type", 1),
            ("pattern_type", 1),
            ("environment", 1),
            ("validation_status", 1),
            ("outcome", 1),
            ("fibonacci_level", 1),
            ("is_super_alert", 1),

            # Compound indexes for common filter combinations
            [("timestamp", -1), ("environment", 1)],
            [("timestamp", -1), ("alert_type", 1)],
            [("timestamp", -1), ("pattern_type", 1)],
            [("symbol", 1), ("timestamp", -1)],
            [("environment", 1), ("pattern_type", 1)],
            [("validation_status", 1), ("timestamp", -1)],
            [("outcome", 1), ("timestamp", -1)],
            [("fibonacci_level", 1), ("alert_type", 1)],
        ]

        for index_spec in indexes_to_create:
            try:
                if isinstance(index_spec, tuple):
                    # Single field index
                    collection.create_index([index_spec])
                else:
                    # Compound index
                    collection.create_index(index_spec)
                logger.info(f"✅ Created index: {index_spec}")
            except Exception as e:
                # Index might already exist
                logger.debug(f"Index creation skipped (may already exist): {index_spec} - {e}")

        logger.info("📊 Pattern validation database indexes ensured")

    except Exception as e:
        logger.error(f"❌ Error ensuring pattern validation indexes: {e}")

def clear_pattern_validation_cache():
    """Clear all pattern validation related cache entries."""
    try:
        if not redis_client:
            return

        # Get all cache keys related to pattern validation
        cache_patterns = [
            "pattern_analytics:*",
            "daily_summary:*"
        ]

        deleted_count = 0
        for pattern in cache_patterns:
            keys = redis_client.keys(pattern)
            if keys:
                deleted_count += redis_client.delete(*keys)

        logger.info(f"🗑️ Cleared {deleted_count} pattern validation cache entries")
        return deleted_count

    except Exception as e:
        logger.error(f"❌ Error clearing pattern validation cache: {e}")
        return 0

def get_alert_by_id(alert_id: str) -> dict:
    """Get a specific alert by its ID."""
    try:
        # Use the alerts collection from mongo_service
        collection = alerts_collection

        # Find the alert by ID
        doc = collection.find_one({"_id": ObjectId(alert_id)})

        if not doc:
            return None

        # Convert MongoDB document to dictionary
        doc['id'] = str(doc['_id'])
        del doc['_id']

        # Ensure all fields have default values for backward compatibility
        doc.setdefault('environment', 'LOCAL')
        doc.setdefault('validation_status', 'PENDING')
        doc.setdefault('validated_by', None)
        doc.setdefault('validation_date', None)
        doc.setdefault('fibonacci_level', None)
        doc.setdefault('pnf_matrix_score', None)
        doc.setdefault('column_number', None)
        doc.setdefault('accuracy_checked', False)
        doc.setdefault('outcome', None)
        doc.setdefault('outcome_price', None)
        doc.setdefault('outcome_date', None)
        doc.setdefault('profit_loss_percent', None)
        doc.setdefault('days_to_outcome', None)
        doc.setdefault('market_conditions', None)
        doc.setdefault('volume_at_alert', None)
        doc.setdefault('notes', None)

        return doc

    except Exception as e:
        logger.error(f"❌ Error fetching alert by ID {alert_id}: {e}")
        return None

def get_detailed_pattern_analysis(pattern_type: str = None, start_date: str = None, end_date: str = None, environment: str = None) -> dict:
    """Get detailed pattern analysis with individual alert breakdown."""
    try:
        # Use the alerts collection from mongo_service
        collection = alerts_collection

        # Build match query
        match_query = {}

        if pattern_type:
            match_query["pattern_type"] = pattern_type

        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = datetime.fromisoformat(start_date + 'T00:00:00')
            if end_date:
                date_query["$lte"] = datetime.fromisoformat(end_date + 'T23:59:59')
            match_query["timestamp"] = date_query

        if environment and environment != "ALL":
            match_query["environment"] = environment

        # Get all matching alerts
        alerts = list(collection.find(match_query).sort("timestamp", -1))

        # Process alerts for analysis
        analysis = {
            "pattern_type": pattern_type or "ALL",
            "total_alerts": len(alerts),
            "success_count": 0,
            "failure_count": 0,
            "pending_count": 0,
            "avg_profit_loss": 0,
            "avg_days_to_outcome": 0,
            "success_rate": 0,
            "win_loss_ratio": 0,
            "confidence_level": "LOW",
            "alerts_by_symbol": {},
            "alerts_by_date": {},
            "fibonacci_performance": {},
            "environment_breakdown": {},
            "recent_alerts": []
        }

        if not alerts:
            return analysis

        # Process each alert
        total_profit_loss = 0
        total_days = 0
        profit_loss_count = 0
        days_count = 0

        for alert in alerts:
            # Convert ObjectId to string
            alert['id'] = str(alert['_id'])
            del alert['_id']

            # Count outcomes
            outcome = alert.get('outcome')
            if outcome == 'SUCCESS':
                analysis['success_count'] += 1
            elif outcome == 'FAILURE':
                analysis['failure_count'] += 1
            else:
                analysis['pending_count'] += 1

            # Accumulate profit/loss
            if alert.get('profit_loss_percent') is not None:
                total_profit_loss += alert['profit_loss_percent']
                profit_loss_count += 1

            # Accumulate days to outcome
            if alert.get('days_to_outcome') is not None:
                total_days += alert['days_to_outcome']
                days_count += 1

            # Group by symbol
            symbol = alert.get('symbol', 'UNKNOWN')
            if symbol not in analysis['alerts_by_symbol']:
                analysis['alerts_by_symbol'][symbol] = {
                    'count': 0,
                    'success': 0,
                    'failure': 0,
                    'pending': 0
                }
            analysis['alerts_by_symbol'][symbol]['count'] += 1
            if outcome == 'SUCCESS':
                analysis['alerts_by_symbol'][symbol]['success'] += 1
            elif outcome == 'FAILURE':
                analysis['alerts_by_symbol'][symbol]['failure'] += 1
            else:
                analysis['alerts_by_symbol'][symbol]['pending'] += 1

            # Group by date
            date_str = alert.get('timestamp', datetime.now()).strftime('%Y-%m-%d')
            if date_str not in analysis['alerts_by_date']:
                analysis['alerts_by_date'][date_str] = 0
            analysis['alerts_by_date'][date_str] += 1

            # Fibonacci level performance
            fib_level = alert.get('fibonacci_level')
            if fib_level:
                if fib_level not in analysis['fibonacci_performance']:
                    analysis['fibonacci_performance'][fib_level] = {
                        'count': 0,
                        'success': 0,
                        'success_rate': 0
                    }
                analysis['fibonacci_performance'][fib_level]['count'] += 1
                if outcome == 'SUCCESS':
                    analysis['fibonacci_performance'][fib_level]['success'] += 1

            # Environment breakdown
            env = alert.get('environment', 'LOCAL')
            if env not in analysis['environment_breakdown']:
                analysis['environment_breakdown'][env] = {
                    'count': 0,
                    'success': 0,
                    'success_rate': 0
                }
            analysis['environment_breakdown'][env]['count'] += 1
            if outcome == 'SUCCESS':
                analysis['environment_breakdown'][env]['success'] += 1

        # Calculate averages and rates
        if profit_loss_count > 0:
            analysis['avg_profit_loss'] = total_profit_loss / profit_loss_count

        if days_count > 0:
            analysis['avg_days_to_outcome'] = total_days / days_count

        total_decided = analysis['success_count'] + analysis['failure_count']
        if total_decided > 0:
            analysis['success_rate'] = (analysis['success_count'] / total_decided) * 100
            analysis['win_loss_ratio'] = analysis['success_count'] / max(analysis['failure_count'], 1)

        # Determine confidence level
        if analysis['success_rate'] >= 60:
            analysis['confidence_level'] = "HIGH"
        elif analysis['success_rate'] >= 45:
            analysis['confidence_level'] = "MEDIUM"
        else:
            analysis['confidence_level'] = "LOW"

        # Calculate Fibonacci performance rates
        for fib_level in analysis['fibonacci_performance']:
            fib_data = analysis['fibonacci_performance'][fib_level]
            if fib_data['count'] > 0:
                fib_data['success_rate'] = (fib_data['success'] / fib_data['count']) * 100

        # Calculate environment performance rates
        for env in analysis['environment_breakdown']:
            env_data = analysis['environment_breakdown'][env]
            if env_data['count'] > 0:
                env_data['success_rate'] = (env_data['success'] / env_data['count']) * 100

        # Get recent alerts (last 10)
        analysis['recent_alerts'] = alerts[:10]

        return analysis

    except Exception as e:
        logger.error(f"❌ Error getting detailed pattern analysis: {e}")
        return {
            "pattern_type": pattern_type or "ALL",
            "total_alerts": 0,
            "success_count": 0,
            "failure_count": 0,
            "pending_count": 0,
            "error": str(e)
        }

def get_available_stocks() -> List[str]:
    """Get list of unique stock symbols from alerts."""
    try:
        # Use the alerts collection from mongo_service
        collection = alerts_collection

        # Get distinct symbols
        stocks = collection.distinct("symbol")

        # Sort and return
        return sorted([stock for stock in stocks if stock])

    except Exception as e:
        logger.error(f"❌ Error fetching available stocks: {e}")
        return []

def get_available_patterns() -> List[str]:
    """Get list of unique pattern types from alerts."""
    try:
        # Use the alerts collection from mongo_service
        collection = alerts_collection

        # Get distinct pattern types
        patterns = collection.distinct("pattern_type")

        # Sort and return
        return sorted([pattern for pattern in patterns if pattern])

    except Exception as e:
        logger.error(f"❌ Error fetching available patterns: {e}")
        return []
