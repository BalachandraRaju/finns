import atexit
import datetime
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app import crud, charts, alerts, telegram_bot
from app.services import get_stock_data_bulk
from app.telegram_bot import send_telegram_alert, send_alert_message, send_enhanced_pattern_telegram
from logzero import logger
import redis
import json

# RSI Configuration from environment variables
RSI_OVERBOUGHT_THRESHOLD = float(os.getenv("RSI_OVERBOUGHT_THRESHOLD", "60"))
RSI_OVERSOLD_THRESHOLD = float(os.getenv("RSI_OVERSOLD_THRESHOLD", "40"))
RSI_PERIOD = int(os.getenv("RSI_PERIOD", "9"))

# Connect to Redis
# This assumes Redis is running on localhost:6379
# This will be used to store the last alert for each stock to avoid repeat notifications.
try:
    redis_client = redis.Redis(decode_responses=True)
    redis_client.ping()
    logger.info("Connected to Redis successfully!")
except redis.exceptions.ConnectionError as e:
    logger.error(f"Could not connect to Redis: {e}. Alerts will not be de-duplicated.")
    redis_client = None

PNF_ALERT_FUNCTIONS = [
    alerts.find_buy_signal,
    alerts.find_sell_signal,
    alerts.find_triple_top_breakout,
    alerts.find_triple_bottom_breakdown,
    alerts.find_ascending_triple_top,
    alerts.find_descending_triple_bottom
]

RSI_ALERT_FUNCTIONS = [
    alerts.find_rsi_overbought_alert,
    alerts.find_rsi_oversold_alert
]

def check_for_alerts():
    """
    This is the main job function that runs on a schedule.
    It iterates through all watchlist stocks, fetches their P&F data,
    checks for all defined alert patterns, and sends notifications.
    Only runs during market hours (9 AM to 3:30 PM IST).

    NEW: Fetches latest LTP data for ALL stocks before running alerts.
    """
    # Check if we're in market hours (9 AM to 3:30 PM IST)
    now = datetime.datetime.now()
    market_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
    market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)

    if not (market_start <= now <= market_end):
        logger.info("Outside market hours (9 AM - 3:30 PM). Skipping alert check.")
        return

    # Skip weekends (Saturday=5, Sunday=6)
    if now.weekday() >= 5:
        logger.info("Weekend detected. Skipping alert check.")
        return

    logger.info("--- Running scheduled alert check ---")

    # STEP 1: Fetch latest LTP data for ALL stocks and update database
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data-fetch'))
        from dhan_live_data_service import dhan_live_data_service

        logger.info("📊 Fetching latest LTP data for all watchlist stocks...")
        data_status = dhan_live_data_service.ensure_latest_data_for_alerts()

        ready_count = sum(1 for ready in data_status.values() if ready)
        total_count = len(data_status)
        logger.info(f"✅ Latest data ready for {ready_count}/{total_count} stocks")

    except Exception as e:
        logger.error(f"❌ Error fetching latest data: {e}")
        logger.warning("⚠️ Continuing with existing database data...")

    # STEP 2: Check alerts for all watchlist stocks
    watchlist = crud.get_watchlist_details()
    if not watchlist:
        logger.info("Watchlist is empty. Skipping alert check.")
        return

    for stock in watchlist:
        symbol = stock.symbol
        instrument_key = stock.instrument_key
        logger.info(f"Checking alerts for {symbol}...")

        # Check P&F alerts using daily data
        check_pnf_alerts(symbol, instrument_key)

        # RSI alerts disabled - will be modified in a different way
        # check_rsi_alerts(symbol, instrument_key)

    logger.info("--- Alert check completed ---")


def check_pnf_alerts(symbol: str, instrument_key: str):
    """
    Check Point & Figure alerts for a stock using enhanced pattern detection.
    Uses 1-minute data with 0.25% box size as requested by user.
    """
    try:
        # User specifications:
        # Box Size: 0.25%
        # Time interval: 1 min
        # Reversal box: 3
        # Data source: 1 month
        box_percentage = 0.0025  # 0.25% box size (PRODUCTION SETTING)
        reversal = 3  # 3-box reversal (PRODUCTION SETTING)

        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=30)  # 1 month of data as requested

        # Get 1-minute candle data using OPTIMIZED approach (minimizes API calls)
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data-fetch'))
            from optimized_data_strategy import get_optimized_data_for_symbol

            # Use optimized strategy that prioritizes LTP over individual API calls
            candles_data = get_optimized_data_for_symbol(symbol, instrument_key)

            # Convert to legacy format for compatibility
            all_candles = []
            for candle in candles_data:
                all_candles.append({
                    'timestamp': candle['timestamp'].isoformat() if hasattr(candle['timestamp'], 'isoformat') else str(candle['timestamp']),
                    'open': candle['open'],
                    'high': candle['high'],
                    'low': candle['low'],
                    'close': candle['close'],
                    'volume': candle['volume']
                })

            if all_candles:
                logger.info(f"✅ Alert check: Retrieved {len(all_candles)} optimized candles for {symbol} (no individual API calls)")
            else:
                logger.warning(f"⚠️ Alert check: No optimized candles retrieved for {symbol}")

        except Exception as e:
            logger.error(f"❌ Error using optimized strategy for alerts, falling back to legacy method: {e}")

            # Fallback to original method
            all_candles = charts.get_candles_for_instrument(instrument_key, "1minute", start_date, today)

        if not all_candles:
            logger.warning(f"No 1-minute candle data for {symbol}, cannot check P&F alerts.")
            return

        # Extract price data for P&F calculation and EMA
        highs = [float(c['high']) for c in all_candles]
        lows = [float(c['low']) for c in all_candles]
        closes = [float(c['close']) for c in all_candles]

        # Calculate P&F points with user specifications
        x_coords, y_coords, pnf_symbols = charts._calculate_pnf_points(highs, lows, box_percentage, reversal)
        if not x_coords:
            logger.info(f"Not enough P&F data to check alerts for {symbol}.")
            return

        # Use enhanced pattern detection with EMA validation
        from app.pattern_detector import PatternDetector
        detector = PatternDetector()

        # Analyze patterns with closing prices for EMA calculation
        alert_triggers = detector.analyze_pattern_formation(x_coords, y_coords, pnf_symbols, closes)

        # Process each alert trigger
        for alert_trigger in alert_triggers:
            # Convert AlertTrigger to alert dictionary format for existing system
            alert_dict = {
                'type': alert_trigger.pattern_type.value.replace('_', ' ').title(),
                'signal_price': alert_trigger.price,
                'pattern_type': alert_trigger.pattern_type.value,
                'alert_type': alert_trigger.alert_type.value,
                'column': alert_trigger.column,
                'trigger_reason': alert_trigger.trigger_reason,
                'is_first_occurrence': alert_trigger.is_first_occurrence
            }

            # Handle the alert (includes Telegram notification and Redis storage)
            handle_enhanced_pattern_alert(symbol, alert_dict)

    except Exception as e:
        logger.error(f"Error checking enhanced P&F alerts for {symbol}: {e}")


def check_rsi_alerts(symbol: str, instrument_key: str):
    """
    Check RSI alerts for a stock using 3-minute data (aggregated from 1-minute).
    """
    try:
        # Use 1-minute data and aggregate to 3-minute for RSI alerts
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=5)  # Get 5 days of 1-minute data

        # Fetch 1-minute candle data and aggregate to 3-minute
        candle_data_1min = charts.get_candles_for_instrument(instrument_key, "1minute", start_date, today)
        candle_data = charts.aggregate_to_3minute(candle_data_1min)

        if not candle_data:
            logger.warning(f"No 3-minute candle data for {symbol}, cannot check RSI alerts.")
            return

        # Check for RSI alerts
        for alert_func in RSI_ALERT_FUNCTIONS:
            if alert_func == alerts.find_rsi_overbought_alert:
                # Check for overbought condition using configured threshold
                alert = alert_func(candle_data, symbol, rsi_threshold=RSI_OVERBOUGHT_THRESHOLD, period=RSI_PERIOD)
            elif alert_func == alerts.find_rsi_oversold_alert:
                # Check for oversold condition using configured threshold
                alert = alert_func(candle_data, symbol, rsi_threshold=RSI_OVERSOLD_THRESHOLD, period=RSI_PERIOD)
            else:
                alert = alert_func(candle_data, symbol)

            if alert:
                handle_alert(symbol, alert)
                # Continue checking other RSI alerts (don't break)

    except Exception as e:
        logger.error(f"Error checking RSI alerts for {symbol}: {e}")


def handle_alert(symbol: str, alert: dict):
    """
    Handles a found alert: checks if it's new, sends a notification,
    saves it to database and Redis to prevent duplicates.
    """
    if not redis_client:
        # If no Redis, we can't check for duplicates, so we just log it.
        logger.warning("No Redis connection, cannot process alert further.")
        return

    alert_type = alert['type']
    signal_price = alert['signal_price']

    # Use a simple key for the latest alert for a given stock and pattern type
    redis_key = f"alert:{symbol}:{alert_type}"
    last_signal_price_str = redis_client.get(redis_key)

    # Check if we have already alerted for this exact signal price
    if last_signal_price_str and float(last_signal_price_str) == signal_price:
        logger.info(f"Duplicate alert found for {symbol} ({alert_type}). Ignoring.")
        return

    logger.info(f"\033[92mNEW ALERT FOUND\033[0m: {symbol} - {alert_type} @ {signal_price:.2f}")

    # Get instrument key for the symbol
    from app.crud import get_stock_by_instrument_key, save_alert
    watchlist = crud.get_watchlist_details()
    instrument_key = None
    for stock in watchlist:
        if stock.symbol == symbol:
            instrument_key = stock.instrument_key
            break

    # Save alert to database
    alert_data = {
        'alert_type': 'BUY' if 'buy' in alert_type.lower() or 'bullish' in alert_type.lower() else 'SELL',
        'pattern_type': alert.get('pattern_type', alert_type.lower().replace(' ', '_')),
        'type': alert_type,
        'signal_price': signal_price,
        'trigger_reason': alert.get('trigger_reason', f"{alert_type} signal at ₹{signal_price}"),
        'column': alert.get('column'),
        'volume': alert.get('volume'),
        'market_conditions': alert.get('market_conditions')
    }

    alert_id = save_alert(symbol, instrument_key, alert_data)
    if alert_id:
        logger.info(f"✅ Alert saved to database with ID: {alert_id}")

    # NOTE: Telegram alerts are sent via handle_enhanced_pattern_alert() for pattern alerts
    # RSI alerts (if enabled) would use send_alert_message()
    # Removed duplicate send_alert_message() call to prevent double alerts

    # Save this new alert to Redis to prevent re-sending
    # Also save it to a general key for display on the watchlist
    redis_client.set(redis_key, signal_price)
    latest_alert_data = {
        'type': alert_type,
        'signal_price': signal_price,
        'timestamp': datetime.datetime.now().isoformat(),
        'alert_id': alert_id  # Include database ID for reference
    }
    redis_client.set(f"latest_alert:{symbol}", json.dumps(latest_alert_data))


def handle_enhanced_pattern_alert(symbol: str, alert_dict: dict):
    """
    Handle enhanced pattern alerts with improved Telegram messaging, database storage and Redis storage.
    Prevents duplicate alerts and sends detailed pattern information.
    Respects user settings for alert types.
    """
    if not redis_client:
        logger.warning("Redis not available. Cannot check for duplicate alerts.")
        return

    # Get user settings to check if alerts are enabled
    settings = crud.get_settings()

    # Check if pattern alerts are enabled
    if not settings.get('enable_pattern_alerts', True):
        logger.info(f"Pattern alerts disabled in settings. Skipping alert for {symbol}")
        return

    pattern_type = alert_dict.get('pattern_type', 'unknown')
    signal_price = alert_dict.get('signal_price', 0)
    trigger_reason = alert_dict.get('trigger_reason', '')
    alert_type = alert_dict.get('alert_type', 'BUY')
    column = alert_dict.get('column', 0)
    is_super_alert = alert_dict.get('is_super_alert', False)

    # Check if only super alerts are enabled
    if settings.get('enable_super_alerts_only', False) and not is_super_alert:
        logger.info(f"Only super alerts enabled. Skipping regular alert for {symbol} - {pattern_type}")
        return

    # Check pattern-specific settings
    pattern_enabled = True
    if 'double_top' in pattern_type or 'double_bottom' in pattern_type:
        pattern_enabled = settings.get('enable_double_top_bottom', True)
    elif 'triple_top' in pattern_type or 'triple_bottom' in pattern_type:
        pattern_enabled = settings.get('enable_triple_top_bottom', True)
    elif 'quadruple_top' in pattern_type or 'quadruple_bottom' in pattern_type:
        pattern_enabled = settings.get('enable_quadruple_top_bottom', True)
    elif 'pole' in pattern_type:
        pattern_enabled = settings.get('enable_pole_patterns', True)
    elif 'catapult' in pattern_type:
        pattern_enabled = settings.get('enable_catapult_patterns', True)

    if not pattern_enabled:
        logger.info(f"Pattern type {pattern_type} disabled in settings. Skipping alert for {symbol}")
        return

    # Create unique Redis key for this specific pattern alert
    redis_key = f"pattern_alert:{symbol}:{pattern_type}"

    # Check if we've already sent this alert
    last_alert_price = redis_client.get(redis_key)
    if last_alert_price:
        last_price = float(last_alert_price)
        # Only send if price has moved significantly (0.5% difference)
        price_diff_pct = abs(signal_price - last_price) / last_price * 100
        if price_diff_pct < 0.5:
            logger.info(f"Skipping duplicate pattern alert for {symbol} - {pattern_type}. Price change: {price_diff_pct:.2f}%")
            return

    logger.info(f"\033[92mNEW PATTERN ALERT\033[0m: {symbol} - {pattern_type} @ {signal_price:.2f}")

    # Get instrument key for the symbol
    from app.crud import save_alert
    watchlist = crud.get_watchlist_details()
    instrument_key = None
    for stock in watchlist:
        if stock.symbol == symbol:
            instrument_key = stock.instrument_key
            break

    # Save enhanced alert to database
    enhanced_alert_data = {
        'alert_type': alert_type,
        'pattern_type': pattern_type,
        'type': alert_dict.get('type', pattern_type.replace('_', ' ').title()),
        'signal_price': signal_price,
        'trigger_reason': trigger_reason,
        'column': column,
        'volume': alert_dict.get('volume'),
        'market_conditions': alert_dict.get('market_conditions')
    }

    alert_id = save_alert(symbol, instrument_key, enhanced_alert_data)
    if alert_id:
        logger.info(f"✅ Enhanced pattern alert saved to database with ID: {alert_id}")

    # Send enhanced Telegram message for pattern alerts (if enabled)
    if settings.get('telegram_alerts_enabled', True):
        send_enhanced_pattern_telegram(symbol, alert_dict)
    else:
        logger.info(f"Telegram alerts disabled. Alert saved to database only.")

    # Save this new alert to Redis to prevent re-sending
    redis_client.set(redis_key, signal_price)

    # Also save to general latest alert key for watchlist display
    latest_alert_data = {
        'type': alert_dict.get('type', pattern_type),
        'signal_price': signal_price,
        'pattern_type': pattern_type,
        'alert_type': alert_type,
        'column': column,
        'trigger_reason': trigger_reason,
        'timestamp': datetime.datetime.now().isoformat()
    }
    redis_client.set(f"latest_alert:{symbol}", json.dumps(latest_alert_data))


def start_scheduler():
    """Initializes and starts the background scheduler."""
    scheduler = BackgroundScheduler(daemon=True)
    
    # Schedule the placeholder job
    scheduler.add_job(check_for_alerts, 'interval', minutes=1)
    
    scheduler.start()
    logger.info("Alert scheduler started. Will run every 1 minute.")
    
    # Shut down the scheduler when the app exits
    atexit.register(lambda: scheduler.shutdown())
