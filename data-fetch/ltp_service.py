"""
LTP (Last Traded Price) data service for real-time stock price collection.
Uses Upstox LTP API v3 for efficient bulk data collection.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from logzero import logger
import time

from app.db import SessionLocal
from app.models import LTPData, DataSyncStatus
from app import crud

# Import Upstox LTP client and F&O stocks loader
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from upstox_ltp_client import upstox_ltp_client
from fo_stocks_loader import fo_stocks_loader

class LTPService:
    """Service for managing LTP data collection and storage using Upstox API."""

    def __init__(self):
        self.upstox_ltp = upstox_ltp_client
        self.fo_loader = fo_stocks_loader
    
    def get_watchlist_symbols(self) -> List[str]:
        """Get trading symbols for all stocks (F&O stocks or existing watchlist)."""
        try:
            # Use F&O stocks loader to get symbols
            symbols = self.fo_loader.get_stock_symbols_for_data_collection()

            if not symbols:
                logger.warning("No stocks found for LTP collection")
                return []

            logger.info(f"📋 Found {len(symbols)} symbols for LTP collection")
            return symbols

        except Exception as e:
            logger.error(f"❌ Error getting watchlist symbols: {e}")
            return []
    
    def _convert_to_angelone_symbol(self, upstox_symbol: str) -> Optional[str]:
        """
        Convert Upstox symbol to AngelOne trading symbol format.
        
        Args:
            upstox_symbol: Upstox symbol (e.g., 'MARUTI')
            
        Returns:
            AngelOne trading symbol (e.g., 'MARUTI-EQ')
        """
        if not upstox_symbol:
            return None
        
        # For equity stocks, append -EQ
        # This is a basic conversion - in production you'd want a proper mapping table
        return f"{upstox_symbol}-EQ"
    
    def collect_ltp_data(self) -> Dict[str, float]:
        """
        Collect LTP data for all watchlist stocks using Upstox LTP API v3.
        Enhanced with detailed logging for optimization tracking.

        Returns:
            Dict mapping symbol to LTP price
        """
        start_time = time.time()
        try:
            logger.info("🚀 Starting LTP collection using Upstox LTP API v3...")
            logger.info("📊 API Strategy: Single call for ALL watchlist stocks")

            # Test Upstox connection first
            if not self.upstox_ltp.test_connection():
                logger.error("❌ Upstox connection failed")
                return {}

            # Get LTP data for all watchlist stocks
            api_start_time = time.time()
            ltp_data = self.upstox_ltp.get_watchlist_ltp()
            api_end_time = time.time()
            api_duration = api_end_time - api_start_time

            if ltp_data:
                logger.info(f"✅ LTP API SUCCESS:")
                logger.info(f"   📊 Stocks fetched: {len(ltp_data)} symbols")
                logger.info(f"   ⏱️ API call duration: {api_duration:.2f} seconds")
                logger.info(f"   🌐 API calls made: 1 (instead of {len(ltp_data)} individual calls)")
                logger.info(f"   💰 API efficiency: {len(ltp_data)}x improvement")

                # Log sample data
                sample_symbols = list(ltp_data.keys())[:3]
                for symbol in sample_symbols:
                    price = ltp_data[symbol].get('last_price', 'N/A')
                    logger.info(f"   📈 {symbol}: ₹{price}")

                if len(ltp_data) > 3:
                    logger.info(f"   📊 ... and {len(ltp_data) - 3} more stocks")

                # Store in database
                db_start_time = time.time()
                self._store_ltp_data(ltp_data)
                db_end_time = time.time()
                db_duration = db_end_time - db_start_time

                logger.info(f"✅ DATABASE STORAGE:")
                logger.info(f"   🗄️ Storage duration: {db_duration:.2f} seconds")
                logger.info(f"   📊 Records stored: {len(ltp_data)}")

                # Return simplified format for compatibility
                simple_ltp = {symbol: data['last_price'] for symbol, data in ltp_data.items()
                             if data.get('last_price')}

                total_duration = time.time() - start_time
                logger.info(f"🎯 LTP COLLECTION COMPLETE:")
                logger.info(f"   ⏱️ Total duration: {total_duration:.2f} seconds")
                logger.info(f"   📊 Success rate: {len(simple_ltp)}/{len(ltp_data)} stocks")

                return simple_ltp
            else:
                logger.warning("❌ No LTP data received from Upstox")
                return {}

        except Exception as e:
            total_duration = time.time() - start_time
            logger.error(f"❌ Error collecting LTP data after {total_duration:.2f}s: {e}")
            return {}

    def test_upstox_connection(self) -> bool:
        """Test Upstox API connection."""
        try:
            return self.upstox_ltp.test_connection()
        except Exception as e:
            logger.error(f"❌ Upstox connection test failed: {e}")
            return False
    
    def _store_ltp_data(self, ltp_data: Dict[str, Dict]) -> None:
        """Store LTP data in database."""
        try:
            db = SessionLocal()
            current_time = datetime.now()

            for symbol, data in ltp_data.items():
                # Extract LTP and other data
                ltp_price = data.get('last_price')
                if not ltp_price:
                    continue

                # Get instrument key for symbol
                stocks = crud.get_all_stocks()
                instrument_key = None
                for stock in stocks:
                    if stock['symbol'] == symbol:
                        instrument_key = stock['instrument_key']
                        break

                # Create LTP record
                ltp_record = LTPData(
                    symbol=symbol,
                    instrument_key=instrument_key,
                    ltp=float(ltp_price),
                    timestamp=current_time,
                    volume=int(data.get('volume', 0)),
                    change=float(data.get('change', 0.0)),
                    change_percent=float(data.get('change_percent', 0.0))
                )
                db.add(ltp_record)
                
                # Update sync status
                sync_status = db.query(DataSyncStatus).filter(
                    DataSyncStatus.symbol == symbol,
                    DataSyncStatus.data_type == 'ltp'
                ).first()
                
                if sync_status:
                    sync_status.last_sync = current_time
                    sync_status.sync_status = 'success'
                    sync_status.records_synced = 1
                    sync_status.error_message = None
                else:
                    sync_status = DataSyncStatus(
                        symbol=symbol,
                        data_type='ltp',
                        last_sync=current_time,
                        sync_status='success',
                        records_synced=1
                    )
                    db.add(sync_status)
            
            db.commit()
            logger.info(f"💾 Stored LTP data for {len(ltp_data)} symbols in database")
            
        except Exception as e:
            logger.error(f"❌ Error storing LTP data: {e}")
            if db:
                db.rollback()
        finally:
            if db:
                db.close()
    
    def get_latest_ltp(self, symbol: str) -> Optional[float]:
        """Get latest LTP for a symbol from database."""
        try:
            db = SessionLocal()
            
            # Convert to AngelOne symbol format
            angelone_symbol = self._convert_to_angelone_symbol(symbol)
            if not angelone_symbol:
                return None
            
            latest_ltp = db.query(LTPData).filter(
                LTPData.symbol == angelone_symbol
            ).order_by(LTPData.timestamp.desc()).first()
            
            if latest_ltp:
                return latest_ltp.ltp
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting latest LTP for {symbol}: {e}")
            return None
        finally:
            if db:
                db.close()
    
    def get_ltp_history(self, symbol: str, hours: int = 24) -> List[Dict]:
        """Get LTP history for a symbol."""
        try:
            db = SessionLocal()
            
            # Convert to AngelOne symbol format
            angelone_symbol = self._convert_to_angelone_symbol(symbol)
            if not angelone_symbol:
                return []
            
            since_time = datetime.now() - timedelta(hours=hours)
            
            ltp_records = db.query(LTPData).filter(
                LTPData.symbol == angelone_symbol,
                LTPData.timestamp >= since_time
            ).order_by(LTPData.timestamp.desc()).all()
            
            return [
                {
                    'timestamp': record.timestamp.isoformat(),
                    'ltp': record.ltp,
                    'symbol': record.symbol
                }
                for record in ltp_records
            ]
            
        except Exception as e:
            logger.error(f"❌ Error getting LTP history for {symbol}: {e}")
            return []
        finally:
            if db:
                db.close()
    
    def check_data_freshness(self) -> Dict[str, Dict]:
        """Check freshness of LTP data for all symbols."""
        try:
            db = SessionLocal()
            symbols = self.get_watchlist_symbols()
            freshness_report = {}
            
            for symbol in symbols:
                sync_status = db.query(DataSyncStatus).filter(
                    DataSyncStatus.symbol == symbol,
                    DataSyncStatus.data_type == 'ltp'
                ).first()
                
                if sync_status:
                    time_since_sync = datetime.now() - sync_status.last_sync
                    freshness_report[symbol] = {
                        'last_sync': sync_status.last_sync.isoformat(),
                        'minutes_ago': int(time_since_sync.total_seconds() / 60),
                        'status': sync_status.sync_status,
                        'is_stale': time_since_sync > timedelta(minutes=5)  # Consider stale after 5 minutes
                    }
                else:
                    freshness_report[symbol] = {
                        'last_sync': None,
                        'minutes_ago': None,
                        'status': 'never_synced',
                        'is_stale': True
                    }
            
            return freshness_report
            
        except Exception as e:
            logger.error(f"❌ Error checking data freshness: {e}")
            return {}
        finally:
            if db:
                db.close()
    
    def test_angelone_connection(self) -> bool:
        """Test AngelOne API connection."""
        return self.angelone.test_connection()

# Global service instance
ltp_service = LTPService()
