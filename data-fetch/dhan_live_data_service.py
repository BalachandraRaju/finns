"""
Dhan Live Data Service
Fetches LTP data for all watchlist stocks and updates database with latest candles.
Supports up to 1000 stocks in a single API call.
"""

import os
import sys
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from logzero import logger

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import Dhan clients
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dhan_ltp_client import dhan_ltp_client
from dhan_historical_client import DhanHistoricalClient
from database_service import database_service


class DhanLiveDataService:
    """Service for collecting live LTP data and updating database."""
    
    def __init__(self):
        self.ltp_client = dhan_ltp_client
        self.historical_client = DhanHistoricalClient()
        self.db_service = database_service
        
    def get_all_watchlist_stocks(self) -> List[Dict]:
        """
        Get all stocks from watchlist with their security IDs.

        Returns:
            List of dicts with keys: symbol, instrument_key, security_id
        """
        try:
            from app import crud

            # Get watchlist details (returns list of WatchlistStock objects)
            watchlist = crud.get_watchlist_details()

            stocks = []
            for stock in watchlist:
                # Handle both WatchlistStock objects and dict-like objects
                if hasattr(stock, 'instrument_key'):
                    # It's a WatchlistStock object
                    instrument_key = stock.instrument_key
                    symbol = stock.symbol
                elif isinstance(stock, dict):
                    # It's a dictionary
                    instrument_key = stock.get('instrument_key', '')
                    symbol = stock.get('symbol', '')
                else:
                    # Unknown type, skip
                    continue

                # Extract security_id from instrument_key (format: DHAN_3518)
                if instrument_key and instrument_key.startswith('DHAN_'):
                    security_id = instrument_key.replace('DHAN_', '')
                    stocks.append({
                        'symbol': symbol,
                        'instrument_key': instrument_key,
                        'security_id': security_id
                    })

            logger.info(f"📋 Found {len(stocks)} stocks in watchlist")
            return stocks

        except Exception as e:
            logger.error(f"❌ Error getting watchlist stocks: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def fetch_and_update_ltp_data(self) -> Dict[str, float]:
        """
        Fetch LTP data for all watchlist stocks in a single API call.
        Updates database with latest 1-minute candles.
        
        Returns:
            Dictionary mapping instrument_key to LTP price
        """
        try:
            # Get all watchlist stocks
            stocks = self.get_all_watchlist_stocks()
            
            if not stocks:
                logger.warning("⚠️ No stocks in watchlist")
                return {}
            
            # Extract security IDs for LTP API call
            security_ids = [stock['security_id'] for stock in stocks]
            
            logger.info(f"📊 Fetching LTP for {len(security_ids)} stocks in single API call...")
            
            # Fetch LTP data (single API call for all stocks)
            ltp_data = self.ltp_client.get_ltp_data(security_ids)
            
            if not ltp_data:
                logger.warning("⚠️ No LTP data received from Dhan API")
                return {}
            
            logger.info(f"✅ Received LTP for {len(ltp_data)} stocks")
            
            # Convert to instrument_key mapping and save to database
            result = {}
            current_time = datetime.now()
            
            # Round to nearest minute for candle timestamp
            candle_timestamp = current_time.replace(second=0, microsecond=0)
            
            for stock in stocks:
                security_id = stock['security_id']
                instrument_key = stock['instrument_key']
                symbol = stock['symbol']
                
                if security_id in ltp_data:
                    ltp_price = ltp_data[security_id]
                    result[instrument_key] = ltp_price
                    
                    # Create 1-minute candle from LTP
                    # For LTP-based candles, all OHLC values are the same
                    candle = {
                        'timestamp': candle_timestamp,
                        'open': ltp_price,
                        'high': ltp_price,
                        'low': ltp_price,
                        'close': ltp_price,
                        'volume': 0  # Volume not available from LTP API
                    }
                    
                    # Save to database using SQLAlchemy
                    try:
                        from app.db import SessionLocal
                        from app.models import Candle

                        db = SessionLocal()
                        try:
                            # Check if candle already exists for this timestamp
                            existing = db.query(Candle).filter(
                                Candle.instrument_key == instrument_key,
                                Candle.interval == '1minute',
                                Candle.timestamp == candle_timestamp
                            ).first()

                            if existing:
                                # Update existing candle
                                existing.open = ltp_price
                                existing.high = ltp_price
                                existing.low = ltp_price
                                existing.close = ltp_price
                                existing.volume = 0
                            else:
                                # Insert new candle
                                new_candle = Candle(
                                    instrument_key=instrument_key,
                                    interval='1minute',
                                    timestamp=candle_timestamp,
                                    open=ltp_price,
                                    high=ltp_price,
                                    low=ltp_price,
                                    close=ltp_price,
                                    volume=0
                                )
                                db.add(new_candle)

                            db.commit()
                            logger.debug(f"💾 Saved LTP candle for {symbol}: ₹{ltp_price:.2f}")
                        finally:
                            db.close()

                    except Exception as e:
                        logger.error(f"❌ Error saving candle for {symbol}: {e}")
            
            logger.info(f"✅ Updated database with {len(result)} LTP candles")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in fetch_and_update_ltp_data: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def backfill_missing_data(self, instrument_key: str, symbol: str, security_id: str) -> bool:
        """
        Backfill missing historical data for a stock.
        Fetches data from market open (9:15 AM) to current time.
        
        Args:
            instrument_key: Instrument key (e.g., DHAN_3518)
            symbol: Stock symbol (e.g., TORNTPHARM)
            security_id: Dhan security ID (e.g., 3518)
            
        Returns:
            True if backfill successful, False otherwise
        """
        try:
            logger.info(f"🔄 Backfilling data for {symbol}...")
            
            # Get today's market hours
            today = datetime.now()
            market_open = today.replace(hour=9, minute=15, second=0, microsecond=0)
            current_time = datetime.now()
            
            # Only backfill if we're past market open
            if current_time < market_open:
                logger.info(f"⏰ Market not yet open, skipping backfill for {symbol}")
                return False
            
            # Fetch historical data from market open to now
            logger.info(f"📊 Fetching historical data for {symbol} from {market_open} to {current_time}")
            
            candles = self.historical_client.get_intraday_data(
                security_id=int(security_id),
                from_date=market_open,
                to_date=current_time,
                interval='1',
                exchange_segment='NSE_EQ',
                instrument='EQUITY',
                stock_symbol=symbol
            )
            
            if not candles:
                logger.warning(f"⚠️ No historical data received for {symbol}")
                return False
            
            # Save all candles to database
            saved_count = 0
            for candle in candles:
                try:
                    self.db_service.save_candle(
                        instrument_key=instrument_key,
                        interval='1minute',
                        candle=candle
                    )
                    saved_count += 1
                except Exception as e:
                    logger.error(f"❌ Error saving candle: {e}")
            
            logger.info(f"✅ Backfilled {saved_count}/{len(candles)} candles for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error backfilling data for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def ensure_latest_data_for_alerts(self) -> Dict[str, bool]:
        """
        Ensure all watchlist stocks have latest data before running alerts.
        
        Strategy:
        1. Fetch LTP for all stocks (single API call)
        2. Check which stocks have stale data (last candle > 5 minutes old)
        3. Backfill missing data for stale stocks
        
        Returns:
            Dictionary mapping instrument_key to data_ready status
        """
        try:
            logger.info("🔍 Ensuring latest data for all watchlist stocks...")
            
            # Step 1: Fetch and update LTP data for all stocks
            ltp_data = self.fetch_and_update_ltp_data()
            
            # Step 2: Check for stale data and backfill if needed
            stocks = self.get_all_watchlist_stocks()
            result = {}
            
            current_time = datetime.now()
            stale_threshold = timedelta(minutes=5)
            
            for stock in stocks:
                instrument_key = stock['instrument_key']
                symbol = stock['symbol']
                security_id = stock['security_id']
                
                # Check last candle timestamp
                try:
                    from datetime import date
                    candles = self.db_service.get_candles_smart(
                        instrument_key=instrument_key,
                        interval='1minute',
                        start_date=date.today(),
                        end_date=date.today(),
                        auto_backfill=False
                    )
                    
                    if candles:
                        last_candle = candles[-1]
                        last_timestamp = last_candle['timestamp']
                        
                        # Check if data is stale
                        if isinstance(last_timestamp, str):
                            last_timestamp = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
                        
                        time_diff = current_time - last_timestamp
                        
                        if time_diff > stale_threshold:
                            logger.warning(f"⚠️ Stale data for {symbol} (last: {last_timestamp}, age: {time_diff})")
                            # Backfill missing data
                            backfill_success = self.backfill_missing_data(instrument_key, symbol, security_id)
                            result[instrument_key] = backfill_success
                        else:
                            logger.debug(f"✅ Fresh data for {symbol} (age: {time_diff})")
                            result[instrument_key] = True
                    else:
                        logger.warning(f"⚠️ No data found for {symbol}, backfilling...")
                        # No data at all, backfill
                        backfill_success = self.backfill_missing_data(instrument_key, symbol, security_id)
                        result[instrument_key] = backfill_success
                        
                except Exception as e:
                    logger.error(f"❌ Error checking data freshness for {symbol}: {e}")
                    result[instrument_key] = False
            
            fresh_count = sum(1 for ready in result.values() if ready)
            logger.info(f"✅ Data ready for {fresh_count}/{len(result)} stocks")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error ensuring latest data: {e}")
            import traceback
            traceback.print_exc()
            return {}


# Global singleton instance
dhan_live_data_service = DhanLiveDataService()


if __name__ == "__main__":
    """Test the Dhan Live Data Service."""
    from dotenv import load_dotenv
    load_dotenv()
    
    print("\n" + "="*80)
    print("🧪 TESTING DHAN LIVE DATA SERVICE")
    print("="*80 + "\n")
    
    # Test 1: Get watchlist stocks
    print("📋 Test 1: Getting watchlist stocks...")
    stocks = dhan_live_data_service.get_all_watchlist_stocks()
    print(f"✅ Found {len(stocks)} stocks")
    if stocks:
        print(f"   Sample: {stocks[0]}\n")
    
    # Test 2: Fetch and update LTP data
    print("📊 Test 2: Fetching LTP data for all stocks...")
    ltp_data = dhan_live_data_service.fetch_and_update_ltp_data()
    print(f"✅ Fetched LTP for {len(ltp_data)} stocks")
    if ltp_data:
        sample_key = list(ltp_data.keys())[0]
        print(f"   Sample: {sample_key} = ₹{ltp_data[sample_key]:.2f}\n")
    
    # Test 3: Ensure latest data
    print("🔍 Test 3: Ensuring latest data for all stocks...")
    result = dhan_live_data_service.ensure_latest_data_for_alerts()
    ready_count = sum(1 for ready in result.values() if ready)
    print(f"✅ Data ready for {ready_count}/{len(result)} stocks\n")
    
    print("="*80)
    print("🏁 TESTING COMPLETE")
    print("="*80 + "\n")

