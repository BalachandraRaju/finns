"""
F&O Stocks Loader for loading NSE F&O stocks from file into database.
Handles stock list management and instrument key mapping.
"""

import sys
import os
import csv
from typing import List, Dict
from logzero import logger

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.db import SessionLocal
from app import crud

class FOStocksLoader:
    """Loader for F&O stocks from NSE file."""
    
    def __init__(self):
        self.fo_stocks_file = os.path.join(project_root, "nse_fo_stock_symbols.txt")
    
    def load_fo_stocks_from_file(self) -> List[str]:
        """Load F&O stock symbols from the text file."""
        try:
            if not os.path.exists(self.fo_stocks_file):
                logger.error(f"❌ F&O stocks file not found: {self.fo_stocks_file}")
                return []
            
            with open(self.fo_stocks_file, 'r') as file:
                content = file.read().strip()
                
                # Parse the comma-separated quoted symbols
                # Remove quotes and split by comma
                symbols = []
                for symbol in content.split(','):
                    symbol = symbol.strip().strip('"')
                    if symbol and not symbol.startswith('NSE'):  # Skip test symbols
                        symbols.append(symbol)
                
                logger.info(f"📋 Loaded {len(symbols)} F&O symbols from file")
                return symbols
                
        except Exception as e:
            logger.error(f"❌ Error loading F&O stocks from file: {e}")
            return []
    
    def get_existing_watchlist_symbols(self) -> List[str]:
        """Get symbols from existing watchlist."""
        try:
            stocks = crud.get_all_stocks()
            symbols = [stock['symbol'] for stock in stocks]
            logger.info(f"📋 Found {len(symbols)} symbols in existing watchlist")
            return symbols
        except Exception as e:
            logger.error(f"❌ Error getting existing watchlist: {e}")
            return []
    
    def get_stock_symbols_for_data_collection(self) -> List[str]:
        """
        Get stock symbols for data collection.
        Priority: 1) Existing watchlist, 2) F&O stocks from file
        """
        try:
            # First try existing watchlist
            existing_symbols = self.get_existing_watchlist_symbols()
            
            if existing_symbols:
                logger.info(f"✅ Using existing watchlist with {len(existing_symbols)} symbols")
                return existing_symbols
            
            # Fallback to F&O stocks from file
            fo_symbols = self.load_fo_stocks_from_file()
            
            if fo_symbols:
                logger.info(f"✅ Using F&O stocks from file with {len(fo_symbols)} symbols")
                return fo_symbols
            
            logger.warning("⚠️ No stock symbols found from any source")
            return []
            
        except Exception as e:
            logger.error(f"❌ Error getting stock symbols: {e}")
            return []
    
    def create_instrument_keys_for_fo_stocks(self, symbols: List[str]) -> Dict[str, str]:
        """
        Create Upstox instrument keys for F&O stocks.
        Format: NSE_EQ|{symbol}
        """
        try:
            instrument_mapping = {}
            
            for symbol in symbols:
                # Upstox instrument key format for NSE equity
                instrument_key = f"NSE_EQ|{symbol}"
                instrument_mapping[symbol] = instrument_key
            
            logger.info(f"📊 Created instrument keys for {len(instrument_mapping)} symbols")
            return instrument_mapping
            
        except Exception as e:
            logger.error(f"❌ Error creating instrument keys: {e}")
            return {}
    
    def add_fo_stocks_to_watchlist(self, symbols: List[str]) -> bool:
        """Add F&O stocks to watchlist if not already present."""
        try:
            existing_symbols = self.get_existing_watchlist_symbols()
            
            # Get symbols that need to be added
            new_symbols = [s for s in symbols if s not in existing_symbols]
            
            if not new_symbols:
                logger.info("✅ All F&O symbols already in watchlist")
                return True
            
            logger.info(f"📝 Adding {len(new_symbols)} new F&O symbols to watchlist")
            
            # Create instrument keys
            instrument_mapping = self.create_instrument_keys_for_fo_stocks(new_symbols)
            
            # Add to watchlist using crud
            added_count = 0
            for symbol in new_symbols:
                try:
                    instrument_key = instrument_mapping.get(symbol)
                    if instrument_key:
                        # Add stock to watchlist
                        # Note: This assumes crud.add_stock exists - you may need to implement this
                        success = crud.add_stock_to_watchlist(
                            instrument_key=instrument_key,
                            symbol=symbol,
                            trade_type="Neutral",
                            tags="F&O"
                        )
                        
                        if success:
                            added_count += 1
                        
                except Exception as e:
                    logger.warning(f"⚠️ Could not add {symbol}: {e}")
                    continue
            
            logger.info(f"✅ Successfully added {added_count}/{len(new_symbols)} F&O symbols to watchlist")
            return added_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error adding F&O stocks to watchlist: {e}")
            return False
    
    def get_fo_symbols_with_instrument_keys(self) -> List[Dict[str, str]]:
        """Get F&O symbols with their instrument keys for data collection."""
        try:
            symbols = self.get_stock_symbols_for_data_collection()
            
            if not symbols:
                return []
            
            # Get existing stocks with instrument keys
            existing_stocks = crud.get_all_stocks()
            stocks_with_keys = []
            
            for stock in existing_stocks:
                if stock['symbol'] in symbols:
                    stocks_with_keys.append({
                        'symbol': stock['symbol'],
                        'instrument_key': stock['instrument_key']
                    })
            
            # For symbols without instrument keys, create them
            existing_symbols = [s['symbol'] for s in stocks_with_keys]
            missing_symbols = [s for s in symbols if s not in existing_symbols]
            
            if missing_symbols:
                logger.info(f"📊 Creating instrument keys for {len(missing_symbols)} missing symbols")
                instrument_mapping = self.create_instrument_keys_for_fo_stocks(missing_symbols)
                
                for symbol in missing_symbols:
                    stocks_with_keys.append({
                        'symbol': symbol,
                        'instrument_key': instrument_mapping.get(symbol, f"NSE_EQ|{symbol}")
                    })
            
            logger.info(f"✅ Prepared {len(stocks_with_keys)} stocks for data collection")
            return stocks_with_keys
            
        except Exception as e:
            logger.error(f"❌ Error getting F&O symbols with instrument keys: {e}")
            return []
    
    def validate_fo_stocks_setup(self) -> bool:
        """Validate that F&O stocks are properly set up for data collection."""
        try:
            stocks = self.get_fo_symbols_with_instrument_keys()
            
            if not stocks:
                logger.error("❌ No stocks available for data collection")
                return False
            
            # Check if all stocks have valid instrument keys
            valid_stocks = 0
            for stock in stocks:
                if stock.get('instrument_key') and stock.get('symbol'):
                    valid_stocks += 1
                else:
                    logger.warning(f"⚠️ Invalid stock data: {stock}")
            
            logger.info(f"✅ Validation: {valid_stocks}/{len(stocks)} stocks have valid data")
            return valid_stocks > 0
            
        except Exception as e:
            logger.error(f"❌ Error validating F&O stocks setup: {e}")
            return False

# Global instance
fo_stocks_loader = FOStocksLoader()
