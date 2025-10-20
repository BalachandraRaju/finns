"""
Dhan Historical Data Backfill Service
Fetches and stores 2 months of 1-minute candle data for F&O stocks.
"""

import os
import sys
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from logzero import logger
import time

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Use MongoDB instead of SQLAlchemy
from app.mongo_service import candles_collection, data_sync_status_collection

# Import Dhan clients
sys.path.insert(0, os.path.join(project_root, 'data-fetch'))
from dhan_historical_client import dhan_historical_client
from dhan_instruments import dhan_instruments


class DhanBackfillService:
    """Service for backfilling historical 1-minute data from Dhan API."""
    
    def __init__(self):
        """Initialize the backfill service."""
        self.historical_client = dhan_historical_client
        self.instruments = dhan_instruments
        
    def load_fo_symbols(self) -> List[str]:
        """
        Load F&O stock symbols from file.

        Returns:
            List of stock symbols
        """
        try:
            symbols_file = os.path.join(project_root, 'nse_fo_stock_symbols.txt')

            with open(symbols_file, 'r') as f:
                content = f.read()
                # Split by comma and clean up
                symbols = [s.strip().strip('"').strip("'") for s in content.split(',') if s.strip()]

                # Filter out test symbols and indices
                filtered_symbols = []
                skip_patterns = ['NSETEST', 'NIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'BANKNIFTY']

                for symbol in symbols:
                    # Skip if symbol contains any skip pattern
                    if any(pattern in symbol for pattern in skip_patterns):
                        continue
                    filtered_symbols.append(symbol)

            logger.info(f"📋 Loaded {len(filtered_symbols)} F&O symbols from file (filtered from {len(symbols)} total)")
            return filtered_symbols

        except Exception as e:
            logger.error(f"❌ Error loading F&O symbols: {e}")
            return []

    def _get_last_candle_timestamp(self, instrument_key: str, interval: str) -> datetime:
        """
        Get the timestamp of the last candle in database for smart backfill.

        IMPORTANT: This operates at the INDIVIDUAL STOCK LEVEL.
        Each stock (instrument_key) has its own last timestamp, allowing
        independent backfilling based on each stock's missing data.

        Args:
            instrument_key: Unique identifier for the stock (e.g., "DHAN_11536")
            interval: Candle interval (e.g., "1minute")

        Returns:
            datetime: Timestamp of the last candle for this specific stock, or None if no data exists
        """
        try:
            # Query filters by BOTH instrument_key AND interval
            # This ensures each stock tracks its own last timestamp independently
            last_candle = candles_collection.find_one(
                {
                    "instrument_key": instrument_key,  # Individual stock level
                    "interval": interval
                },
                sort=[("timestamp", -1)]
            )

            if last_candle:
                return last_candle['timestamp']
            return None
        except Exception as e:
            logger.error(f"❌ Error getting last candle timestamp: {e}")
            return None

    def backfill_stock(
        self,
        symbol: str,
        months_back: int = 2,
        interval: str = "1minute"
    ) -> bool:
        """
        Backfill historical data for a single stock.
        
        Args:
            symbol: Stock symbol (e.g., "TCS", "RELIANCE")
            months_back: Number of months of historical data to fetch
            interval: Candle interval (default: "1minute")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"📊 Starting backfill for {symbol}...")
            
            # Get Dhan security ID for symbol
            security_id = self.instruments.get_security_id(symbol)
            
            if not security_id:
                logger.warning(f"⚠️  No security ID found for {symbol} - skipping")
                self._update_sync_status(symbol, 'intraday', 'failed', 0, 'No security ID found')
                return False
            
            logger.info(f"   Security ID: {security_id}")
            instrument_key = f"DHAN_{security_id}"

            # Smart date range calculation - only fetch missing data
            to_date = datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)

            # Check for last candle in database
            last_candle_ts = self._get_last_candle_timestamp(instrument_key, interval)

            if last_candle_ts:
                # Incremental backfill - only fetch from last candle to now
                from_date = last_candle_ts + timedelta(minutes=1)
                logger.info(f"   📈 Incremental backfill from last candle: {last_candle_ts}")
                logger.info(f"   Fetching only missing data from {from_date} to {to_date}")
            else:
                # Initial backfill - fetch full history
                from_date = to_date - timedelta(days=months_back * 30)
                from_date = from_date.replace(hour=9, minute=15, second=0, microsecond=0)
                logger.info(f"   📊 Initial backfill (no existing data)")

            logger.info(f"   Date range: {from_date.date()} to {to_date.date()}")
            
            # Fetch historical data from Dhan
            candles = self.historical_client.get_intraday_data(
                security_id=security_id,
                from_date=from_date,
                to_date=to_date,
                interval="1"  # 1-minute candles
            )
            
            if not candles:
                logger.warning(f"⚠️  No data received for {symbol}")
                self._update_sync_status(symbol, 'intraday', 'failed', 0, 'No data received from API')
                return False
            
            logger.info(f"   Fetched {len(candles)} candles from Dhan API")
            
            # Store candles in database
            records_stored = self._store_candles(symbol, security_id, candles, interval)
            
            if records_stored > 0:
                logger.info(f"✅ Successfully stored {records_stored} candles for {symbol}")
                self._update_sync_status(symbol, 'intraday', 'success', records_stored)
                return True
            else:
                logger.error(f"❌ Failed to store candles for {symbol}")
                self._update_sync_status(symbol, 'intraday', 'failed', 0, 'Database storage failed')
                return False
                
        except Exception as e:
            logger.error(f"❌ Error during backfill for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            self._update_sync_status(symbol, 'intraday', 'failed', 0, str(e))
            return False
    
    def _store_candles(
        self,
        symbol: str,
        security_id: int,
        candles: List[Dict],
        interval: str
    ) -> int:
        """
        Store candles in MongoDB database.

        Args:
            symbol: Stock symbol
            security_id: Dhan security ID
            candles: List of candle dictionaries
            interval: Candle interval

        Returns:
            Number of records stored
        """
        try:
            records_stored = 0

            # Use security_id as instrument_key for Dhan data
            instrument_key = f"DHAN_{security_id}"

            for candle_data in candles:
                try:
                    # Check if candle already exists
                    existing = candles_collection.find_one({
                        "instrument_key": instrument_key,
                        "interval": interval,
                        "timestamp": candle_data['timestamp']
                    })

                    if existing:
                        # Update existing candle
                        candles_collection.update_one(
                            {"_id": existing["_id"]},
                            {"$set": {
                                "open": candle_data['open'],
                                "high": candle_data['high'],
                                "low": candle_data['low'],
                                "close": candle_data['close'],
                                "volume": candle_data['volume'],
                                "oi": 0
                            }}
                        )
                    else:
                        # Insert new candle
                        candles_collection.insert_one({
                            "instrument_key": instrument_key,
                            "interval": interval,
                            "timestamp": candle_data['timestamp'],
                            "open": candle_data['open'],
                            "high": candle_data['high'],
                            "low": candle_data['low'],
                            "close": candle_data['close'],
                            "volume": candle_data['volume'],
                            "oi": 0  # No OI for equity
                        })

                    records_stored += 1

                except Exception as e:
                    logger.debug(f"Skipping duplicate or invalid candle: {e}")
                    continue

            logger.info(f"   💾 Stored {records_stored} new/updated records to database")
            return records_stored

        except Exception as e:
            logger.error(f"❌ Error storing candles for {symbol}: {e}")
            return 0
    
    def _update_sync_status(
        self,
        symbol: str,
        data_type: str,
        status: str,
        records_synced: int = 0,
        error_message: str = None
    ):
        """Update data sync status in database."""
        try:
            sync_status = data_sync_status_collection.find_one({
                "symbol": symbol,
                "data_type": data_type
            })

            if sync_status:
                data_sync_status_collection.update_one(
                    {"_id": sync_status["_id"]},
                    {"$set": {
                        "last_sync": datetime.now(),
                        "sync_status": status,
                        "records_synced": records_synced,
                        "error_message": error_message
                    }}
                )
            else:
                data_sync_status_collection.insert_one({
                    "symbol": symbol,
                    "data_type": data_type,
                    "last_sync": datetime.now(),
                    "sync_status": status,
                    "records_synced": records_synced,
                    "error_message": error_message
                })

        except Exception as e:
            logger.error(f"❌ Error updating sync status: {e}")
    
    def backfill_all_stocks(
        self,
        symbols: List[str] = None,
        months_back: int = 2,
        delay_seconds: int = 1
    ):
        """
        Backfill historical data for multiple stocks.
        
        Args:
            symbols: List of symbols to backfill (None = all F&O stocks)
            months_back: Number of months of historical data
            delay_seconds: Delay between API calls to avoid rate limits
        """
        if symbols is None:
            symbols = self.load_fo_symbols()
        
        total_symbols = len(symbols)
        successful = 0
        failed = 0
        skipped = 0
        
        logger.info("=" * 70)
        logger.info(f"🚀 STARTING BACKFILL FOR {total_symbols} STOCKS")
        logger.info(f"   Date range: Last {months_back} months")
        logger.info(f"   Interval: 1-minute candles")
        logger.info("=" * 70)
        print()
        
        start_time = datetime.now()
        
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"\n[{i}/{total_symbols}] Processing {symbol}...")
            
            result = self.backfill_stock(symbol, months_back)
            
            if result:
                successful += 1
            else:
                # Check if it was skipped (no security ID) or failed
                security_id = self.instruments.get_security_id(symbol)
                if not security_id:
                    skipped += 1
                else:
                    failed += 1
            
            # Add delay to avoid rate limits
            if i < total_symbols:
                time.sleep(delay_seconds)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Print summary
        print()
        logger.info("=" * 70)
        logger.info("📊 BACKFILL SUMMARY")
        logger.info("=" * 70)
        logger.info(f"   Total stocks: {total_symbols}")
        logger.info(f"   ✅ Successful: {successful}")
        logger.info(f"   ❌ Failed: {failed}")
        logger.info(f"   ⚠️  Skipped: {skipped}")
        logger.info(f"   ⏱️  Duration: {duration}")
        logger.info("=" * 70)


# Singleton instance
dhan_backfill_service = DhanBackfillService()


# Test code
if __name__ == "__main__":
    print("=" * 70)
    print("🧪 TESTING DHAN BACKFILL SERVICE")
    print("=" * 70)
    print()
    
    # Test with a few stocks first
    test_symbols = ["TCS", "RELIANCE", "INFY"]
    
    print(f"Testing with {len(test_symbols)} stocks: {', '.join(test_symbols)}")
    print()
    
    dhan_backfill_service.backfill_all_stocks(
        symbols=test_symbols,
        months_back=2,
        delay_seconds=2
    )

