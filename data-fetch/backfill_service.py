"""
Historical data backfill service for filling missing data gaps.
Automatically detects and fills missing historical data using AngelOne API.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, date
from logzero import logger

# Use MongoDB instead of SQLAlchemy
from app.mongo_service import candles_collection, data_sync_status_collection
from app import crud

# Import Upstox client for historical data (working API)
from app.charts import api_client
import upstox_client

class BackfillService:
    """Service for detecting and filling missing 1-minute historical data."""

    def __init__(self):
        # Initialize Upstox API client
        self.api_client = api_client
        self.history_api = upstox_client.HistoryApi(api_client)

        # Import F&O stocks loader
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from fo_stocks_loader import fo_stocks_loader
        self.fo_loader = fo_stocks_loader
    
    def detect_missing_1min_data(self, symbol: str, days_back: int = 30) -> List[Tuple[datetime, datetime]]:
        """
        Detect missing 1-minute data gaps for a symbol.

        Args:
            symbol: Stock symbol
            days_back: Number of days to check back

        Returns:
            List of (start_datetime, end_datetime) tuples representing missing data ranges
        """
        try:
            db = SessionLocal()

            # Get instrument key for symbol using F&O loader
            stocks_with_keys = self.fo_loader.get_fo_symbols_with_instrument_keys()
            instrument_key = None

            for stock in stocks_with_keys:
                if stock['symbol'] == symbol:
                    instrument_key = stock['instrument_key']
                    break

            if not instrument_key:
                logger.warning(f"No instrument key found for symbol {symbol}")
                return []

            # Check for missing 1-minute data
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)

            # Get existing 1-minute candle data
            existing_candles = db.query(Candle).filter(
                Candle.instrument_key == instrument_key,
                Candle.interval == '1minute',
                Candle.timestamp >= datetime.combine(start_date, datetime.min.time()),
                Candle.timestamp <= datetime.combine(end_date, datetime.max.time())
            ).order_by(Candle.timestamp).all()

            # Convert to set of datetime minutes
            existing_minutes = set()
            for candle in existing_candles:
                # Round to minute
                minute_timestamp = candle.timestamp.replace(second=0, microsecond=0)
                existing_minutes.add(minute_timestamp)

            # Find missing minute ranges during market hours (9:15 AM to 3:30 PM)
            missing_ranges = []
            current_date = start_date

            while current_date <= end_date:
                # Skip weekends
                if current_date.weekday() < 5:  # Monday=0 to Friday=4
                    # Market hours: 9:15 AM to 3:30 PM
                    market_start = datetime.combine(current_date, datetime.min.time().replace(hour=9, minute=15))
                    market_end = datetime.combine(current_date, datetime.min.time().replace(hour=15, minute=30))

                    # Check each minute in market hours
                    current_minute = market_start
                    range_start = None

                    while current_minute <= market_end:
                        if current_minute not in existing_minutes:
                            if range_start is None:
                                range_start = current_minute
                        else:
                            if range_start is not None:
                                missing_ranges.append((range_start, current_minute - timedelta(minutes=1)))
                                range_start = None

                        current_minute += timedelta(minutes=1)

                    # Handle case where missing range extends to market close
                    if range_start is not None:
                        missing_ranges.append((range_start, market_end))

                current_date += timedelta(days=1)

            logger.info(f"📊 Found {len(missing_ranges)} missing 1-minute data ranges for {symbol}")
            return missing_ranges

        except Exception as e:
            logger.error(f"❌ Error detecting missing 1-minute data for {symbol}: {e}")
            return []
        finally:
            if db:
                db.close()

    def detect_missing_data(self, symbol: str, days_back: int = 30) -> List[Tuple[date, date]]:
        """Legacy method - now redirects to 1-minute data detection."""
        # Convert 1-minute ranges to daily ranges for compatibility
        minute_ranges = self.detect_missing_1min_data(symbol, days_back)
        daily_ranges = []

        if minute_ranges:
            # Group by date
            dates_with_missing_data = set()
            for start_dt, end_dt in minute_ranges:
                current_date = start_dt.date()
                while current_date <= end_dt.date():
                    dates_with_missing_data.add(current_date)
                    current_date += timedelta(days=1)

            # Convert to ranges
            sorted_dates = sorted(dates_with_missing_data)
            if sorted_dates:
                range_start = sorted_dates[0]
                prev_date = sorted_dates[0]

                for current_date in sorted_dates[1:]:
                    if current_date - prev_date > timedelta(days=1):
                        daily_ranges.append((range_start, prev_date))
                        range_start = current_date
                    prev_date = current_date

                daily_ranges.append((range_start, prev_date))

        return daily_ranges
    
    def backfill_symbol(self, symbol: str, force: bool = False) -> bool:
        """
        Backfill missing historical data for a symbol.
        
        Args:
            symbol: Stock symbol to backfill
            force: Force backfill even if recently synced
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"🔄 Starting backfill for {symbol}")
            
            # Check if backfill is needed (unless forced)
            if not force and not self._needs_backfill(symbol):
                logger.info(f"✅ {symbol} data is up to date, skipping backfill")
                return True
            
            # Detect missing data ranges
            missing_ranges = self.detect_missing_data(symbol, days_back=60)  # Check 2 months back
            
            if not missing_ranges:
                logger.info(f"✅ No missing data found for {symbol}")
                self._update_sync_status(symbol, 'historical', 'success', 0)
                return True
            
            total_records = 0

            # Backfill each missing range using Upstox
            for start_date, end_date in missing_ranges:
                logger.info(f"📈 Backfilling {symbol} from {start_date} to {end_date}")

                # Fetch historical data from Upstox (working API)
                candles = self._fetch_upstox_historical_data(
                    symbol,  # Stock symbol
                    start_date,
                    end_date,
                    'day'  # Daily interval
                )
                
                if candles:
                    # Convert and store candles (Upstox format)
                    records_stored = self._store_upstox_candles(symbol, candles)
                    total_records += records_stored
                    logger.info(f"✅ Stored {records_stored} candles for {symbol} ({start_date} to {end_date})")
                else:
                    logger.warning(f"⚠️ No data received for {symbol} ({start_date} to {end_date})")
            
            # Update sync status
            self._update_sync_status(symbol, 'historical', 'success', total_records)
            logger.info(f"✅ Backfill completed for {symbol}: {total_records} total records")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during backfill for {symbol}: {e}")
            self._update_sync_status(symbol, 'historical', 'failed', 0, str(e))
            return False
    
    def _store_upstox_candles(self, symbol: str, candles: List[Dict]) -> int:
        """Store Upstox historical candles in database."""
        try:
            db = SessionLocal()

            # Get instrument key
            stocks = crud.get_all_stocks()
            instrument_key = None
            for stock in stocks:
                if stock['symbol'] == symbol:
                    instrument_key = stock['instrument_key']
                    break

            if not instrument_key:
                logger.error(f"No instrument key found for {symbol}")
                return 0

            records_stored = 0

            for candle_data in candles:
                # Upstox candle format: dict with timestamp, open, high, low, close, volume
                if isinstance(candle_data, dict) and 'timestamp' in candle_data:
                    # Parse timestamp
                    timestamp_str = candle_data['timestamp']
                    if isinstance(timestamp_str, str):
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        timestamp = datetime.fromtimestamp(timestamp_str / 1000)  # Convert from milliseconds

                    candle = Candle(
                        instrument_key=instrument_key,
                        interval='day',
                        timestamp=timestamp,
                        open=float(candle_data.get('open', 0)),
                        high=float(candle_data.get('high', 0)),
                        low=float(candle_data.get('low', 0)),
                        close=float(candle_data.get('close', 0)),
                        volume=int(candle_data.get('volume', 0))
                    )

                    # Use merge to handle duplicates
                    db.merge(candle)
                    records_stored += 1

            db.commit()
            return records_stored

        except Exception as e:
            logger.error(f"❌ Error storing Upstox candles for {symbol}: {e}")
            if db:
                db.rollback()
            return 0
        finally:
            if db:
                db.close()
    
    def _needs_backfill(self, symbol: str) -> bool:
        """Check if symbol needs backfill based on sync status."""
        try:
            db = SessionLocal()
            
            sync_status = db.query(DataSyncStatus).filter(
                DataSyncStatus.symbol == symbol,
                DataSyncStatus.data_type == 'historical'
            ).first()
            
            if not sync_status:
                return True  # Never synced
            
            if sync_status.sync_status == 'failed':
                return True  # Last sync failed
            
            # Check if last sync was more than 1 day ago
            time_since_sync = datetime.now() - sync_status.last_sync
            return time_since_sync > timedelta(days=1)
            
        except Exception as e:
            logger.error(f"❌ Error checking backfill need for {symbol}: {e}")
            return True  # Default to needing backfill
        finally:
            if db:
                db.close()
    

    
    def _update_sync_status(self, symbol: str, data_type: str, status: str, 
                          records_synced: int, error_message: str = None) -> None:
        """Update sync status for a symbol."""
        try:
            db = SessionLocal()
            
            sync_status = db.query(DataSyncStatus).filter(
                DataSyncStatus.symbol == symbol,
                DataSyncStatus.data_type == data_type
            ).first()
            
            if sync_status:
                sync_status.last_sync = datetime.now()
                sync_status.sync_status = status
                sync_status.records_synced = records_synced
                sync_status.error_message = error_message
            else:
                sync_status = DataSyncStatus(
                    symbol=symbol,
                    data_type=data_type,
                    last_sync=datetime.now(),
                    sync_status=status,
                    records_synced=records_synced,
                    error_message=error_message
                )
                db.add(sync_status)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"❌ Error updating sync status: {e}")
            if db:
                db.rollback()
        finally:
            if db:
                db.close()
    
    def backfill_all_symbols(self, force: bool = False) -> Dict[str, bool]:
        """Backfill all symbols in watchlist."""
        try:
            stocks = crud.get_all_stocks()
            results = {}
            
            for stock in stocks:
                symbol = stock['symbol']
                logger.info(f"🔄 Processing backfill for {symbol}")
                results[symbol] = self.backfill_symbol(symbol, force)
            
            successful = sum(1 for success in results.values() if success)
            logger.info(f"✅ Backfill completed: {successful}/{len(results)} symbols successful")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error during bulk backfill: {e}")
            return {}
    
    def get_sync_status_report(self) -> Dict[str, Dict]:
        """Get sync status report for all symbols."""
        try:
            db = SessionLocal()
            stocks = crud.get_all_stocks()
            report = {}
            
            for stock in stocks:
                symbol = stock['symbol']
                
                # Get sync status for different data types
                sync_statuses = db.query(DataSyncStatus).filter(
                    DataSyncStatus.symbol == symbol
                ).all()
                
                symbol_report = {}
                for sync_status in sync_statuses:
                    symbol_report[sync_status.data_type] = {
                        'last_sync': sync_status.last_sync.isoformat() if sync_status.last_sync else None,
                        'status': sync_status.sync_status,
                        'records_synced': sync_status.records_synced,
                        'error_message': sync_status.error_message
                    }
                
                report[symbol] = symbol_report
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Error generating sync status report: {e}")
            return {}
        finally:
            if db:
                db.close()

    def backfill_all_symbols_1min(self, days_back: int = 60, force: bool = False) -> Dict[str, bool]:
        """
        Backfill missing 1-minute data for all F&O symbols.

        Args:
            days_back: Number of days to backfill (default 60 for 2 months)
            force: If True, force backfill even if recent data exists

        Returns:
            Dictionary mapping symbol to success status
        """
        try:
            # Get F&O symbols with instrument keys
            stocks_with_keys = self.fo_loader.get_fo_symbols_with_instrument_keys()

            if not stocks_with_keys:
                logger.warning("No F&O stocks found for 1-minute backfill")
                return {}

            results = {}

            for stock in stocks_with_keys:
                symbol = stock['symbol']
                instrument_key = stock['instrument_key']

                try:
                    logger.info(f"🔄 Starting 1-minute backfill for {symbol} (past {days_back} days)")

                    if force or self._needs_1min_backfill(symbol, days_back):
                        success = self.backfill_symbol_1min(symbol, instrument_key, days_back)
                        results[symbol] = success

                        if success:
                            logger.info(f"✅ 1-minute backfill completed for {symbol}")
                        else:
                            logger.error(f"❌ 1-minute backfill failed for {symbol}")
                    else:
                        logger.info(f"⏭️ Skipping {symbol} - recent 1-minute data exists")
                        results[symbol] = True

                except Exception as e:
                    logger.error(f"❌ Error during 1-minute backfill for {symbol}: {e}")
                    results[symbol] = False

            successful = sum(1 for success in results.values() if success)
            logger.info(f"📊 1-minute backfill summary: {successful}/{len(results)} symbols successful")

            return results

        except Exception as e:
            logger.error(f"❌ Error during bulk 1-minute backfill: {e}")
            return {}

    def backfill_symbol_1min(self, symbol: str, instrument_key: str, days_back: int = 60) -> bool:
        """
        Backfill 1-minute historical data for a symbol.

        Args:
            symbol: Stock symbol
            instrument_key: Upstox instrument key
            days_back: Number of days to backfill

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"🔄 Starting 1-minute backfill for {symbol} (past {days_back} days)")

            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)

            total_records = 0

            # Backfill day by day to avoid large API calls
            current_date = start_date
            while current_date <= end_date:
                # Skip weekends
                if current_date.weekday() < 5:  # Monday=0 to Friday=4
                    try:
                        logger.info(f"📈 Fetching 1-minute data for {symbol} on {current_date}")

                        # Fetch 1-minute data from Upstox
                        candles = self._fetch_upstox_historical_data(
                            symbol,
                            current_date,
                            current_date,
                            '1minute'  # 1-minute interval
                        )

                        if candles:
                            # Store candles
                            records_stored = self._store_upstox_candles_1min(
                                symbol, instrument_key, candles, '1minute'
                            )
                            total_records += records_stored
                            logger.info(f"✅ Stored {records_stored} 1-minute records for {symbol} on {current_date}")
                        else:
                            logger.warning(f"⚠️ No 1-minute data received for {symbol} on {current_date}")

                    except Exception as e:
                        logger.error(f"❌ Error fetching 1-minute data for {symbol} on {current_date}: {e}")
                        continue

                current_date += timedelta(days=1)

            # Update sync status
            if total_records > 0:
                self._update_sync_status(symbol, '1minute', 'success', total_records)
                logger.info(f"✅ 1-minute backfill completed for {symbol}: {total_records} records")
                return True
            else:
                self._update_sync_status(symbol, '1minute', 'failed', 0, "No data received")
                logger.warning(f"⚠️ No 1-minute data backfilled for {symbol}")
                return False

        except Exception as e:
            logger.error(f"❌ Error during 1-minute backfill for {symbol}: {e}")
            self._update_sync_status(symbol, '1minute', 'failed', 0, str(e))
            return False

    def _store_upstox_candles_1min(self, symbol: str, instrument_key: str,
                                   candles: List[Dict], interval: str) -> int:
        """Store 1-minute Upstox candles in database."""
        try:
            db = SessionLocal()
            records_stored = 0

            for candle_data in candles:
                # Parse Upstox candle format
                timestamp_str = candle_data.get('datetime')
                if not timestamp_str:
                    continue

                # Parse timestamp (Upstox format: "2024-01-15T09:15:00+05:30")
                timestamp = datetime.fromisoformat(timestamp_str.replace('+05:30', ''))

                # Create candle record
                candle = Candle(
                    instrument_key=instrument_key,
                    interval=interval,
                    timestamp=timestamp,
                    open=float(candle_data.get('open', 0)),
                    high=float(candle_data.get('high', 0)),
                    low=float(candle_data.get('low', 0)),
                    close=float(candle_data.get('close', 0)),
                    volume=int(candle_data.get('volume', 0)),
                    oi=int(candle_data.get('oi', 0))
                )

                # Use merge to handle duplicates
                db.merge(candle)
                records_stored += 1

            db.commit()
            return records_stored

        except Exception as e:
            logger.error(f"❌ Error storing 1-minute Upstox candles for {symbol}: {e}")
            if db:
                db.rollback()
            return 0
        finally:
            if db:
                db.close()

    def _needs_1min_backfill(self, symbol: str, days_back: int) -> bool:
        """Check if symbol needs 1-minute backfill."""
        try:
            db = SessionLocal()

            # Check if we have recent 1-minute data
            cutoff_time = datetime.now() - timedelta(days=1)  # Check last day

            # Get instrument key
            stocks_with_keys = self.fo_loader.get_fo_symbols_with_instrument_keys()
            instrument_key = None

            for stock in stocks_with_keys:
                if stock['symbol'] == symbol:
                    instrument_key = stock['instrument_key']
                    break

            if not instrument_key:
                return True  # Need backfill if no instrument key

            # Check for recent 1-minute data
            recent_candles = db.query(Candle).filter(
                Candle.instrument_key == instrument_key,
                Candle.interval == '1minute',
                Candle.timestamp >= cutoff_time
            ).count()

            # If we have recent data, check sync status
            if recent_candles > 0:
                sync_status = db.query(DataSyncStatus).filter(
                    DataSyncStatus.symbol == symbol,
                    DataSyncStatus.data_type == '1minute'
                ).first()

                if sync_status and sync_status.sync_status == 'success':
                    time_since_sync = datetime.now() - sync_status.last_sync
                    return time_since_sync > timedelta(hours=6)  # Backfill if more than 6 hours old

            return True  # Need backfill

        except Exception as e:
            logger.error(f"❌ Error checking 1-minute backfill need for {symbol}: {e}")
            return True
        finally:
            if db:
                db.close()

    def _fetch_upstox_historical_data(self, symbol: str, start_date: date, end_date: date, interval: str) -> List[Dict]:
        """
        Fetch historical data from Upstox API.

        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            interval: Data interval ('day', '1minute', etc.)

        Returns:
            List of candle dictionaries
        """
        try:
            # Get instrument key for symbol
            stocks_with_keys = self.fo_loader.get_fo_symbols_with_instrument_keys()
            instrument_key = None

            for stock in stocks_with_keys:
                if stock['symbol'] == symbol:
                    instrument_key = stock['instrument_key']
                    break

            if not instrument_key:
                logger.error(f"❌ No instrument key found for symbol {symbol}")
                return []

            logger.info(f"📈 Fetching {interval} data for {symbol} ({instrument_key}) from {start_date} to {end_date}")

            # Use Upstox API based on interval
            if interval == '1minute':
                # For intraday data, use intraday API
                api_response = self.history_api.get_intra_day_candle_data(
                    instrument_key=instrument_key,
                    interval=interval,
                    api_version="v2"
                )
            else:
                # For historical data, use historical API
                api_response = self.history_api.get_historical_candle_data(
                    instrument_key=instrument_key,
                    interval=interval,
                    to_date=end_date.strftime('%Y-%m-%d'),
                    from_date=start_date.strftime('%Y-%m-%d'),
                    api_version="v2"
                )

            if api_response.status == 'success' and api_response.data.candles:
                candles = []
                for candle_data in api_response.data.candles:
                    # Convert Upstox candle format to our format
                    candle = {
                        'datetime': candle_data[0],  # Timestamp
                        'open': float(candle_data[1]),
                        'high': float(candle_data[2]),
                        'low': float(candle_data[3]),
                        'close': float(candle_data[4]),
                        'volume': int(candle_data[5]),
                        'oi': int(candle_data[6]) if len(candle_data) > 6 else 0
                    }
                    candles.append(candle)

                logger.info(f"✅ Fetched {len(candles)} {interval} candles for {symbol}")
                return candles
            else:
                logger.warning(f"⚠️ No {interval} data available for {symbol}")
                return []

        except Exception as e:
            logger.error(f"❌ Error fetching {interval} data for {symbol}: {e}")
            return []

# Global service instance
backfill_service = BackfillService()
