"""
Database-First Data Service
Centralized service for all data access with automatic backfill when data is missing.
Powers test-charts, PnF matrix, alerts, and all chart generation from database.
"""

import sys
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, date
from logzero import logger

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Use MongoDB instead of SQLAlchemy
from app.mongo_service import candles_collection, ltp_data_collection
from app import crud

# Import data collection services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from backfill_service import backfill_service  # Legacy Upstox backfill
from dhan_backfill_service import dhan_backfill_service  # New Dhan backfill
from ltp_service import ltp_service
from fo_stocks_loader import fo_stocks_loader

class DatabaseService:
    """
    Database-first service for all data access.
    Automatically handles missing data by triggering backfill operations.
    Now uses Dhan API for all data fetching.
    """

    def __init__(self):
        self.backfill_service = backfill_service  # Legacy Upstox (deprecated)
        self.dhan_backfill_service = dhan_backfill_service  # Primary Dhan backfill
        self.ltp_service = ltp_service
        self.fo_loader = fo_stocks_loader
    
    def get_candles_smart(self, instrument_key: str, interval: str,
                         start_date: date, end_date: date,
                         auto_backfill: bool = True) -> List[Dict]:
        """
        Smart candle data retrieval with optimized API usage.

        Args:
            instrument_key: Stock instrument key
            interval: Data interval ('day', '1minute', '3minute', etc.)
            start_date: Start date
            end_date: End date
            auto_backfill: Whether to automatically backfill missing data

        Returns:
            List of candle dictionaries
        """
        try:
            logger.info(f"📊 Getting {interval} candles for {instrument_key} from {start_date} to {end_date}")

            # 1. Try to get data from database first
            candles = self._get_candles_from_db(instrument_key, interval, start_date, end_date)

            # 2. If no data found and auto_backfill is enabled, trigger automatic backfill
            if not candles and auto_backfill:
                logger.info(f"📭 No data found for {instrument_key}, triggering automatic backfill...")
                self._auto_backfill_missing_data(instrument_key, interval, start_date, end_date)
                # Re-fetch after backfill
                candles = self._get_candles_from_db(instrument_key, interval, start_date, end_date)

            # 3. For intraday data, use optimized strategy to minimize API calls
            if interval == "1minute" and auto_backfill and candles:
                # Use optimized strategy for intraday data
                try:
                    from optimized_data_strategy import optimized_strategy
                    optimized_candles = optimized_strategy.smart_intraday_data_access(instrument_key)

                    if optimized_candles and len(optimized_candles) > len(candles):
                        logger.info(f"🚀 Using optimized strategy: {len(optimized_candles)} candles")
                        candles = optimized_candles

                except Exception as opt_error:
                    logger.warning(f"⚠️ Optimized strategy failed, using standard approach: {opt_error}")

            # 3. For daily data, only backfill if really necessary
            elif interval == "day" and auto_backfill:
                missing_ranges = self._detect_missing_candle_ranges(
                    candles, interval, start_date, end_date
                )

                # Only backfill if we have significant gaps (more than 5 days missing)
                significant_gaps = [
                    (start, end) for start, end in missing_ranges
                    if (end - start).days > 5
                ]

                if significant_gaps:
                    logger.info(f"🔄 Found {len(significant_gaps)} significant gaps, triggering limited backfill...")

                    # Get symbol for backfill
                    symbol = self._get_symbol_from_instrument_key(instrument_key)

                    if symbol:
                        # Only backfill significant gaps to minimize API calls
                        self._backfill_missing_ranges(symbol, instrument_key, significant_gaps[:2], interval)  # Max 2 ranges

                        # Re-fetch data from database
                        candles = self._get_candles_from_db(instrument_key, interval, start_date, end_date)

            # 4. Handle special intervals (3minute aggregation)
            if interval == "3minute" and candles:
                candles = self._aggregate_to_3minute(candles)

            logger.info(f"✅ Retrieved {len(candles)} {interval} candles for {instrument_key}")
            return candles

        except Exception as e:
            logger.error(f"❌ Error getting candles for {instrument_key}: {e}")
            return []
    
    def get_latest_ltp(self, symbol: str, auto_collect: bool = True) -> Optional[float]:
        """
        Get latest LTP for a symbol with automatic collection if stale.

        Args:
            symbol: Stock symbol
            auto_collect: Whether to automatically collect fresh LTP if stale

        Returns:
            Latest LTP price or None
        """
        try:
            # Check database for recent LTP
            # Get LTP from last 5 minutes
            cutoff_time = datetime.now() - timedelta(minutes=5)

            latest_ltp = ltp_data_collection.find_one(
                {
                    "symbol": symbol,
                    "timestamp": {"$gte": cutoff_time}
                },
                sort=[("timestamp", -1)]
            )

            if latest_ltp:
                logger.info(f"📈 Found recent LTP for {symbol}: ₹{latest_ltp['ltp']}")
                return latest_ltp['ltp']

            # If no recent data and auto_collect is enabled
            if auto_collect:
                logger.info(f"🔄 No recent LTP for {symbol}, triggering collection...")

                # Trigger LTP collection
                ltp_data = self.ltp_service.collect_ltp_data()

                if symbol in ltp_data:
                    logger.info(f"✅ Collected fresh LTP for {symbol}: ₹{ltp_data[symbol]}")
                    return ltp_data[symbol]

            logger.warning(f"⚠️ No LTP data available for {symbol}")
            return None

        except Exception as e:
            logger.error(f"❌ Error getting LTP for {symbol}: {e}")
            return None
    
    def get_intraday_candles_smart(self, instrument_key: str, interval: str = "1minute") -> List[Dict]:
        """
        Get intraday candles with smart data management.
        Prioritizes LTP data over historical API calls for efficiency.
        """
        try:
            today = date.today()

            # For intraday, prioritize recent LTP data over historical backfill
            # This avoids excessive API calls for current data

            # First, try to get existing data without triggering backfill
            candles = self.get_candles_smart(
                instrument_key=instrument_key,
                interval=interval,
                start_date=today - timedelta(days=7),  # Get past week for context
                end_date=today,
                auto_backfill=False  # Don't trigger backfill for intraday
            )

            # If we have some recent data, use it
            if candles:
                logger.info(f"✅ Using existing {len(candles)} intraday candles for {instrument_key}")
                return candles

            # Only trigger backfill if we have NO recent data at all
            logger.info(f"🔄 No recent intraday data found, triggering limited backfill for {instrument_key}")
            candles = self.get_candles_smart(
                instrument_key=instrument_key,
                interval=interval,
                start_date=today - timedelta(days=2),  # Only 2 days to minimize API calls
                end_date=today,
                auto_backfill=True
            )

            return candles

        except Exception as e:
            logger.error(f"❌ Error getting intraday candles for {instrument_key}: {e}")
            return []
    
    def get_historical_candles_smart(self, instrument_key: str, interval: str = "day", 
                                   months_back: int = 2) -> List[Dict]:
        """
        Get historical candles for specified period with smart data management.
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=months_back * 30)
            
            return self.get_candles_smart(
                instrument_key=instrument_key,
                interval=interval,
                start_date=start_date,
                end_date=end_date,
                auto_backfill=True
            )
            
        except Exception as e:
            logger.error(f"❌ Error getting historical candles for {instrument_key}: {e}")
            return []
    
    def _get_candles_from_db(self, instrument_key: str, interval: str,
                           start_date: date, end_date: date) -> List[Dict]:
        """Get candles from database."""
        try:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())

            candles = candles_collection.find(
                {
                    "instrument_key": instrument_key,
                    "interval": interval,
                    "timestamp": {
                        "$gte": start_datetime,
                        "$lte": end_datetime
                    }
                }
            ).sort("timestamp", 1)

            # Convert to dictionary format
            candle_dicts = []
            for candle in candles:
                candle_dicts.append({
                    'timestamp': candle['timestamp'],
                    'open': candle['open'],
                    'high': candle['high'],
                    'low': candle['low'],
                    'close': candle['close'],
                    'volume': candle.get('volume', 0),
                    'oi': candle.get('oi', 0)
                })

            return candle_dicts

        except Exception as e:
            logger.error(f"❌ Error getting candles from DB: {e}")
            return []
    
    def _detect_missing_candle_ranges(self, candles: List[Dict], interval: str, 
                                    start_date: date, end_date: date) -> List[Tuple[date, date]]:
        """Detect missing data ranges in candle data."""
        try:
            if not candles:
                return [(start_date, end_date)]
            
            # For 1-minute data, check for gaps during market hours
            if interval == "1minute":
                return self._detect_missing_minute_ranges(candles, start_date, end_date)
            
            # For daily data, check for missing trading days
            existing_dates = set()
            for candle in candles:
                existing_dates.add(candle['timestamp'].date())
            
            missing_ranges = []
            current_date = start_date
            range_start = None
            
            while current_date <= end_date:
                # Skip weekends
                if current_date.weekday() < 5:  # Monday=0 to Friday=4
                    if current_date not in existing_dates:
                        if range_start is None:
                            range_start = current_date
                    else:
                        if range_start is not None:
                            missing_ranges.append((range_start, current_date - timedelta(days=1)))
                            range_start = None
                
                current_date += timedelta(days=1)
            
            # Handle case where missing range extends to end
            if range_start is not None:
                missing_ranges.append((range_start, end_date))
            
            return missing_ranges
            
        except Exception as e:
            logger.error(f"❌ Error detecting missing ranges: {e}")
            return []
    
    def _detect_missing_minute_ranges(self, candles: List[Dict], 
                                    start_date: date, end_date: date) -> List[Tuple[date, date]]:
        """Detect missing minute-level data ranges."""
        try:
            # Convert candles to set of minute timestamps
            existing_minutes = set()
            for candle in candles:
                minute_timestamp = candle['timestamp'].replace(second=0, microsecond=0)
                existing_minutes.add(minute_timestamp)
            
            # Check for missing minutes during market hours
            missing_dates = set()
            current_date = start_date
            
            while current_date <= end_date:
                if current_date.weekday() < 5:  # Skip weekends
                    # Market hours: 9:15 AM to 3:30 PM
                    market_start = datetime.combine(current_date, datetime.min.time().replace(hour=9, minute=15))
                    market_end = datetime.combine(current_date, datetime.min.time().replace(hour=15, minute=30))
                    
                    # Check if we have sufficient data for this day
                    day_minutes = []
                    current_minute = market_start
                    while current_minute <= market_end:
                        if current_minute in existing_minutes:
                            day_minutes.append(current_minute)
                        current_minute += timedelta(minutes=1)
                    
                    # If less than 50% of market minutes are present, consider day missing
                    expected_minutes = (market_end - market_start).total_seconds() / 60
                    if len(day_minutes) < expected_minutes * 0.5:
                        missing_dates.add(current_date)
                
                current_date += timedelta(days=1)
            
            # Convert missing dates to ranges
            if not missing_dates:
                return []
            
            sorted_dates = sorted(missing_dates)
            ranges = []
            range_start = sorted_dates[0]
            prev_date = sorted_dates[0]
            
            for current_date in sorted_dates[1:]:
                if current_date - prev_date > timedelta(days=1):
                    ranges.append((range_start, prev_date))
                    range_start = current_date
                prev_date = current_date
            
            ranges.append((range_start, prev_date))
            return ranges
            
        except Exception as e:
            logger.error(f"❌ Error detecting missing minute ranges: {e}")
            return []
    
    def _get_symbol_from_instrument_key(self, instrument_key: str) -> Optional[str]:
        """Get symbol from instrument key."""
        try:
            # Try from F&O stocks first
            stocks_with_keys = self.fo_loader.get_fo_symbols_with_instrument_keys()
            
            for stock in stocks_with_keys:
                if stock['instrument_key'] == instrument_key:
                    return stock['symbol']
            
            # Try from existing watchlist
            stocks = crud.get_all_stocks()
            for stock in stocks:
                if stock['instrument_key'] == instrument_key:
                    return stock['symbol']
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting symbol for {instrument_key}: {e}")
            return None
    
    def _auto_backfill_missing_data(self, instrument_key: str, interval: str,
                                   start_date: date, end_date: date):
        """
        Automatically backfill missing data when no data is found in database.
        Uses Dhan API for Dhan instrument keys, Upstox for legacy keys.
        """
        try:
            # Get symbol from instrument key
            symbol = self._get_symbol_from_instrument_key(instrument_key)
            if not symbol:
                logger.warning(f"⚠️ Could not determine symbol for {instrument_key}, skipping backfill")
                return

            # Check if this is a Dhan instrument key
            is_dhan_key = instrument_key.startswith('DHAN_')

            if is_dhan_key:
                # Use Dhan backfill service
                if interval == "1minute":
                    # For 1-minute data, backfill 2 months (as per requirement)
                    logger.info(f"🔄 Auto-backfilling 2 months of 1-minute data for {symbol} using Dhan API")
                    self.dhan_backfill_service.backfill_stock(symbol, months_back=2)
                else:
                    # For daily data, backfill 2 months
                    logger.info(f"🔄 Auto-backfilling 2 months of daily data for {symbol} using Dhan API")
                    self.dhan_backfill_service.backfill_stock(symbol, months_back=2)
            else:
                # Legacy Upstox backfill
                logger.warning(f"⚠️ Using legacy Upstox backfill for {symbol} - consider migrating to Dhan")
                if interval == "1minute":
                    days_back = (end_date - start_date).days + 1
                    self.backfill_service.backfill_symbol_1min(symbol, instrument_key, days_back)
                else:
                    self.backfill_service.backfill_symbol(symbol)

        except Exception as e:
            logger.error(f"❌ Error during auto-backfill: {e}")

    def _backfill_missing_ranges(self, symbol: str, instrument_key: str,
                               missing_ranges: List[Tuple[date, date]], interval: str):
        """
        Trigger backfill for missing data ranges using Dhan API.
        Automatically fetches historical data when gaps are detected.
        """
        try:
            # Check if this is a Dhan instrument key
            is_dhan_key = instrument_key.startswith('DHAN_')

            for start_date, end_date in missing_ranges:
                logger.info(f"🔄 Backfilling {interval} data for {symbol} from {start_date} to {end_date}")

                if is_dhan_key:
                    # Use Dhan backfill service for Dhan instrument keys
                    if interval == "1minute":
                        # Calculate months back from date range
                        days_diff = (end_date - start_date).days
                        months_back = max(1, (days_diff // 30) + 1)  # Convert days to months

                        logger.info(f"🔄 Using Dhan API to backfill {months_back} months of 1-minute data for {symbol}")
                        self.dhan_backfill_service.backfill_stock(symbol, months_back=months_back)
                    else:
                        # For daily data, use 2 months default
                        logger.info(f"🔄 Using Dhan API to backfill daily data for {symbol}")
                        self.dhan_backfill_service.backfill_stock(symbol, months_back=2)
                else:
                    # Legacy Upstox backfill (deprecated)
                    logger.warning(f"⚠️ Using legacy Upstox backfill for {symbol} - consider migrating to Dhan")
                    if interval == "1minute":
                        days_back = (end_date - start_date).days + 1
                        self.backfill_service.backfill_symbol_1min(symbol, instrument_key, days_back)
                    else:
                        self.backfill_service.backfill_symbol(symbol)

        except Exception as e:
            logger.error(f"❌ Error during backfill: {e}")
    
    def _aggregate_to_3minute(self, candles_1min: List[Dict]) -> List[Dict]:
        """Aggregate 1-minute candles to 3-minute candles."""
        try:
            if not candles_1min:
                return []
            
            aggregated = []
            current_group = []
            
            for candle in candles_1min:
                current_group.append(candle)
                
                # Group every 3 candles
                if len(current_group) == 3:
                    # Create aggregated candle
                    agg_candle = {
                        'timestamp': current_group[0]['timestamp'],  # Use first timestamp
                        'open': current_group[0]['open'],
                        'high': max(c['high'] for c in current_group),
                        'low': min(c['low'] for c in current_group),
                        'close': current_group[-1]['close'],
                        'volume': sum(c['volume'] for c in current_group),
                        'oi': current_group[-1]['oi']  # Use last OI
                    }
                    aggregated.append(agg_candle)
                    current_group = []
            
            # Handle remaining candles
            if current_group:
                agg_candle = {
                    'timestamp': current_group[0]['timestamp'],
                    'open': current_group[0]['open'],
                    'high': max(c['high'] for c in current_group),
                    'low': min(c['low'] for c in current_group),
                    'close': current_group[-1]['close'],
                    'volume': sum(c['volume'] for c in current_group),
                    'oi': current_group[-1]['oi']
                }
                aggregated.append(agg_candle)
            
            return aggregated
            
        except Exception as e:
            logger.error(f"❌ Error aggregating to 3-minute: {e}")
            return candles_1min

# Global service instance
database_service = DatabaseService()
