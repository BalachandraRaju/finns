"""
Upstox LTP Client for real-time Last Traded Price data collection.
Uses Upstox LTP API v3 which supports up to 500 instruments per request.
"""

import os
import sys
import requests
from typing import List, Dict, Optional
from datetime import datetime
from logzero import logger

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import crud

class UpstoxLTPClient:
    """Upstox client for LTP data collection using LTP API v3."""
    
    def __init__(self):
        self.access_token = os.getenv("UPSTOX_ACCESS_TOKEN")
        self.base_url = "https://api.upstox.com/v2"
        
        if not self.access_token:
            logger.warning("⚠️ UPSTOX_ACCESS_TOKEN not found in environment variables")
    
    def test_connection(self) -> bool:
        """Test Upstox API connection."""
        try:
            if not self.access_token:
                logger.error("❌ No Upstox access token available")
                return False
            
            # Test with a simple API call
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json'
            }
            
            response = requests.get(f"{self.base_url}/user/profile", headers=headers, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Upstox connection test successful")
                return True
            else:
                logger.error(f"❌ Upstox connection test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Upstox connection test error: {e}")
            return False
    
    def get_ltp_data(self, instrument_keys: List[str]) -> Dict[str, Dict]:
        """
        Get LTP data for multiple instruments using Upstox LTP API v3.
        
        Args:
            instrument_keys: List of instrument keys (max 500)
            
        Returns:
            Dict mapping instrument_key to LTP data
        """
        try:
            if not self.access_token:
                logger.error("❌ No Upstox access token available")
                return {}
            
            if len(instrument_keys) > 500:
                logger.warning(f"⚠️ Too many instruments ({len(instrument_keys)}). Upstox supports max 500 per request.")
                instrument_keys = instrument_keys[:500]
            
            if not instrument_keys:
                logger.warning("⚠️ No instrument keys provided")
                return {}
            
            # Prepare API request
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json'
            }
            
            # Join instrument keys with comma
            instrument_keys_str = ','.join(instrument_keys)
            
            params = {
                'instrument_key': instrument_keys_str
            }
            
            logger.info(f"📊 Fetching LTP for {len(instrument_keys)} instruments...")
            
            # Make API request
            response = requests.get(
                f"{self.base_url}/market-quote/ltp",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    ltp_data = data.get('data', {})
                    logger.info(f"✅ Successfully fetched LTP for {len(ltp_data)} instruments")
                    return ltp_data
                else:
                    logger.error(f"❌ LTP API returned error: {data}")
                    return {}
            else:
                logger.error(f"❌ LTP API request failed: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Error fetching LTP data: {e}")
            return {}
    
    def get_watchlist_ltp(self) -> Dict[str, Dict]:
        """Get LTP data for all stocks in the watchlist."""
        try:
            # Get all stocks from watchlist
            stocks = crud.get_all_stocks()
            if not stocks:
                logger.warning("⚠️ No stocks found in watchlist")
                return {}
            
            # Extract instrument keys
            instrument_keys = [stock['instrument_key'] for stock in stocks if stock.get('instrument_key')]
            
            if not instrument_keys:
                logger.warning("⚠️ No instrument keys found in watchlist")
                return {}
            
            logger.info(f"📋 Getting LTP for {len(instrument_keys)} watchlist stocks")
            
            # Fetch LTP data
            ltp_data = self.get_ltp_data(instrument_keys)
            
            # Add symbol mapping for easier access
            enhanced_data = {}
            for stock in stocks:
                instrument_key = stock.get('instrument_key')
                if instrument_key and instrument_key in ltp_data:
                    enhanced_data[stock['symbol']] = {
                        'instrument_key': instrument_key,
                        'ltp_data': ltp_data[instrument_key],
                        'last_price': ltp_data[instrument_key].get('last_price'),
                        'volume': ltp_data[instrument_key].get('volume'),
                        'ltq': ltp_data[instrument_key].get('ltq'),  # Last traded quantity
                        'cp': ltp_data[instrument_key].get('cp'),   # Previous close
                        'change': None,
                        'change_percent': None
                    }
                    
                    # Calculate change and change percentage
                    last_price = enhanced_data[stock['symbol']]['last_price']
                    prev_close = enhanced_data[stock['symbol']]['cp']
                    
                    if last_price and prev_close:
                        change = last_price - prev_close
                        change_percent = (change / prev_close) * 100
                        enhanced_data[stock['symbol']]['change'] = round(change, 2)
                        enhanced_data[stock['symbol']]['change_percent'] = round(change_percent, 2)
            
            logger.info(f"✅ Enhanced LTP data for {len(enhanced_data)} stocks")
            return enhanced_data
            
        except Exception as e:
            logger.error(f"❌ Error getting watchlist LTP: {e}")
            return {}
    
    def get_batch_ltp(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Get LTP data for specific symbols.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dict mapping symbol to LTP data
        """
        try:
            # Get stocks data to map symbols to instrument keys
            stocks = crud.get_all_stocks()
            symbol_to_instrument = {stock['symbol']: stock['instrument_key'] 
                                  for stock in stocks if stock.get('instrument_key')}
            
            # Filter requested symbols and get their instrument keys
            instrument_keys = []
            valid_symbols = []
            
            for symbol in symbols:
                if symbol in symbol_to_instrument:
                    instrument_keys.append(symbol_to_instrument[symbol])
                    valid_symbols.append(symbol)
                else:
                    logger.warning(f"⚠️ Symbol {symbol} not found in watchlist")
            
            if not instrument_keys:
                logger.warning("⚠️ No valid symbols found")
                return {}
            
            # Fetch LTP data
            ltp_data = self.get_ltp_data(instrument_keys)
            
            # Map back to symbols
            result = {}
            for symbol in valid_symbols:
                instrument_key = symbol_to_instrument[symbol]
                if instrument_key in ltp_data:
                    result[symbol] = {
                        'instrument_key': instrument_key,
                        'ltp_data': ltp_data[instrument_key],
                        'last_price': ltp_data[instrument_key].get('last_price'),
                        'volume': ltp_data[instrument_key].get('volume'),
                        'ltq': ltp_data[instrument_key].get('ltq'),
                        'cp': ltp_data[instrument_key].get('cp')
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting batch LTP: {e}")
            return {}

# Global client instance
upstox_ltp_client = UpstoxLTPClient()
