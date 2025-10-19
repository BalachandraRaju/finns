"""
Optimized Data Collection Strategy
Minimizes API calls by prioritizing LTP over individual historical calls.
"""

import sys
import os
from typing import Dict, List
from datetime import datetime, date, timedelta
from logzero import logger

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ltp_service import ltp_service
from backfill_service import backfill_service
from fo_stocks_loader import fo_stocks_loader

class OptimizedDataStrategy:
    """
    Optimized data collection strategy that minimizes API calls.
    
    Strategy:
    1. Use LTP API (1 call for all stocks) for real-time data
    2. Minimize individual historical API calls
    3. Batch backfill operations
    4. Prioritize database over API calls
    """
    
    def __init__(self):
        self.ltp_service = ltp_service
        self.backfill_service = backfill_service
        self.fo_loader = fo_stocks_loader
    
    def collect_real_time_data(self) -> Dict[str, float]:
        """
        Collect real-time LTP data for ALL stocks in a single API call.
        This is the most efficient way to get current prices.
        """
        try:
            logger.info("📊 Collecting real-time LTP data (single API call for all stocks)...")
            
            # Single API call for all stocks
            ltp_data = self.ltp_service.collect_ltp_data()
            
            if ltp_data:
                logger.info(f"✅ Successfully collected LTP for {len(ltp_data)} stocks in 1 API call")
                return ltp_data
            else:
                logger.warning("⚠️ No LTP data received")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Error collecting real-time data: {e}")
            return {}
    
    def smart_intraday_data_access(self, instrument_key: str) -> List[Dict]:
        """
        Smart intraday data access that avoids unnecessary API calls.
        
        Strategy:
        1. Check database first
        2. If no recent data, use LTP for current price
        3. Only use historical API as last resort
        """
        try:
            from database_service import database_service
            
            # Get existing data without triggering backfill
            candles = database_service.get_candles_smart(
                instrument_key=instrument_key,
                interval="1minute",
                start_date=date.today() - timedelta(days=5),
                end_date=date.today(),
                auto_backfill=False  # Key: Don't trigger individual API calls
            )
            
            if candles:
                logger.info(f"✅ Using existing database data: {len(candles)} candles for {instrument_key}")
                return candles
            
            # If no database data, create synthetic candles from LTP
            logger.info(f"🔄 No database data, using LTP-based approach for {instrument_key}")
            return self._create_synthetic_candles_from_ltp(instrument_key)
            
        except Exception as e:
            logger.error(f"❌ Error in smart intraday access: {e}")
            return []
    
    def _create_synthetic_candles_from_ltp(self, instrument_key: str) -> List[Dict]:
        """
        Create synthetic candle data from LTP when historical data is not available.
        This avoids making individual API calls for each stock.
        """
        try:
            # Get symbol from instrument key
            symbol = self._get_symbol_from_instrument_key(instrument_key)
            if not symbol:
                return []
            
            # Get current LTP
            ltp_data = self.ltp_service.collect_ltp_data()
            
            if symbol in ltp_data:
                current_price = ltp_data[symbol]
                current_time = datetime.now()
                
                # Create a simple synthetic candle for current time
                synthetic_candle = {
                    'timestamp': current_time,
                    'open': current_price,
                    'high': current_price,
                    'low': current_price,
                    'close': current_price,
                    'volume': 0  # No volume data from LTP
                }
                
                logger.info(f"📊 Created synthetic candle from LTP for {symbol}: ₹{current_price}")
                return [synthetic_candle]
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Error creating synthetic candles: {e}")
            return []
    
    def batch_historical_backfill(self, symbols: List[str], max_api_calls: int = 5) -> Dict[str, bool]:
        """
        Batch historical backfill with API call limits.
        Only backfill the most important stocks to avoid rate limits.
        """
        try:
            logger.info(f"🔄 Starting batch backfill for {len(symbols)} symbols (max {max_api_calls} API calls)")
            
            results = {}
            api_calls_made = 0
            
            # Prioritize stocks by importance (you can customize this logic)
            prioritized_symbols = self._prioritize_symbols_for_backfill(symbols)
            
            for symbol in prioritized_symbols:
                if api_calls_made >= max_api_calls:
                    logger.warning(f"⚠️ Reached API call limit ({max_api_calls}), stopping backfill")
                    break
                
                try:
                    # Get instrument key
                    stocks_with_keys = self.fo_loader.get_fo_symbols_with_instrument_keys()
                    instrument_key = None
                    
                    for stock in stocks_with_keys:
                        if stock['symbol'] == symbol:
                            instrument_key = stock['instrument_key']
                            break
                    
                    if instrument_key:
                        # Backfill only 1 day to minimize API calls
                        success = self.backfill_service.backfill_symbol_1min(
                            symbol=symbol,
                            instrument_key=instrument_key,
                            days_back=1  # Only 1 day to minimize calls
                        )
                        results[symbol] = success
                        api_calls_made += 1
                        
                        logger.info(f"📈 Backfilled {symbol}: {'✅' if success else '❌'} (API call {api_calls_made}/{max_api_calls})")
                    else:
                        results[symbol] = False
                        
                except Exception as e:
                    logger.error(f"❌ Error backfilling {symbol}: {e}")
                    results[symbol] = False
            
            successful = sum(1 for success in results.values() if success)
            logger.info(f"✅ Batch backfill completed: {successful}/{len(results)} successful, {api_calls_made} API calls made")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in batch backfill: {e}")
            return {}
    
    def _prioritize_symbols_for_backfill(self, symbols: List[str]) -> List[str]:
        """
        Prioritize symbols for backfill based on importance.
        You can customize this logic based on your trading strategy.
        """
        # For now, just return the first few symbols
        # In production, you might prioritize based on:
        # - Trading volume
        # - Recent alert activity
        # - User watchlist preferences
        return symbols[:10]  # Only top 10 to minimize API calls
    
    def _get_symbol_from_instrument_key(self, instrument_key: str) -> str:
        """Get symbol from instrument key."""
        try:
            stocks_with_keys = self.fo_loader.get_fo_symbols_with_instrument_keys()
            
            for stock in stocks_with_keys:
                if stock['instrument_key'] == instrument_key:
                    return stock['symbol']
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting symbol for {instrument_key}: {e}")
            return None
    
    def get_optimized_data_for_alerts(self, symbols: List[str]) -> Dict[str, List[Dict]]:
        """
        Get optimized data for alert processing.
        Minimizes API calls while ensuring we have enough data for alerts.
        """
        try:
            logger.info(f"🚨 Getting optimized data for {len(symbols)} symbols for alerts")
            
            # Step 1: Collect fresh LTP data for all symbols (1 API call)
            ltp_data = self.collect_real_time_data()
            
            # Step 2: Get existing database data for all symbols (no API calls)
            alert_data = {}
            
            for symbol in symbols:
                # Get instrument key
                stocks_with_keys = self.fo_loader.get_fo_symbols_with_instrument_keys()
                instrument_key = None
                
                for stock in stocks_with_keys:
                    if stock['symbol'] == symbol:
                        instrument_key = stock['instrument_key']
                        break
                
                if instrument_key:
                    # Get smart intraday data (prioritizes database)
                    candles = self.smart_intraday_data_access(instrument_key)
                    alert_data[symbol] = candles
            
            logger.info(f"✅ Optimized alert data ready for {len(alert_data)} symbols")
            return alert_data
            
        except Exception as e:
            logger.error(f"❌ Error getting optimized alert data: {e}")
            return {}
    
    def run_optimized_collection_cycle(self):
        """
        Run one optimized data collection cycle.
        This should be called every minute during market hours.
        """
        try:
            logger.info("🔄 Running optimized data collection cycle...")
            
            # Step 1: Collect LTP for all stocks (1 API call)
            ltp_data = self.collect_real_time_data()
            
            if ltp_data:
                logger.info(f"✅ Cycle complete: LTP data for {len(ltp_data)} stocks in 1 API call")
            else:
                logger.warning("⚠️ Cycle complete: No LTP data collected")
            
            # Step 2: Optional minimal backfill (only if really needed)
            # This runs much less frequently to avoid API limits
            
            return len(ltp_data) > 0
            
        except Exception as e:
            logger.error(f"❌ Error in optimized collection cycle: {e}")
            return False

# Global instance
optimized_strategy = OptimizedDataStrategy()

def get_optimized_data_for_symbol(symbol: str, instrument_key: str) -> List[Dict]:
    """
    Public function to get optimized data for a single symbol.
    This should be used by charts, PnF matrix, and alerts.
    """
    return optimized_strategy.smart_intraday_data_access(instrument_key)

def run_optimized_ltp_collection() -> bool:
    """
    Public function to run optimized LTP collection.
    This should be called every minute during market hours.
    """
    return optimized_strategy.run_optimized_collection_cycle()

def get_optimized_alert_data(symbols: List[str]) -> Dict[str, List[Dict]]:
    """
    Public function to get optimized data for alert processing.
    """
    return optimized_strategy.get_optimized_data_for_alerts(symbols)
