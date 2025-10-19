"""
Dhan Instruments Mapper
Downloads and parses Dhan's instrument list to map stock symbols to security IDs.
"""

import os
import sys
import requests
import csv
from typing import Dict, Optional, List
from logzero import logger
import json

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class DhanInstruments:
    """Manages Dhan instrument mappings."""
    
    INSTRUMENT_URL = "https://images.dhan.co/api-data/api-scrip-master.csv"
    CACHE_FILE = "data-fetch/dhan_instruments_cache.json"
    
    def __init__(self):
        self.instruments = {}
        self.symbol_to_security_id = {}
        self.load_instruments()
    
    def download_instruments(self) -> bool:
        """Download instrument list from Dhan."""
        try:
            logger.info("📥 Downloading Dhan instrument list...")
            
            response = requests.get(self.INSTRUMENT_URL, timeout=30)
            
            if response.status_code == 200:
                logger.info("✅ Successfully downloaded instrument list")
                
                # Parse CSV
                lines = response.text.strip().split('\n')
                reader = csv.DictReader(lines)
                
                instruments = []
                for row in reader:
                    instruments.append(row)
                
                logger.info(f"📊 Parsed {len(instruments)} instruments")
                
                # Save to cache
                self._save_cache(instruments)
                
                return True
            else:
                logger.error(f"❌ Failed to download instruments: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error downloading instruments: {e}")
            return False
    
    def _save_cache(self, instruments: List[Dict]):
        """Save instruments to cache file."""
        try:
            cache_data = {
                'instruments': instruments,
                'timestamp': str(os.path.getmtime(__file__) if os.path.exists(__file__) else 0)
            }
            
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"💾 Saved instruments to cache: {self.CACHE_FILE}")
            
        except Exception as e:
            logger.error(f"❌ Error saving cache: {e}")
    
    def _load_cache(self) -> Optional[List[Dict]]:
        """Load instruments from cache file."""
        try:
            if not os.path.exists(self.CACHE_FILE):
                return None
            
            with open(self.CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
            
            instruments = cache_data.get('instruments', [])
            logger.info(f"📂 Loaded {len(instruments)} instruments from cache")
            
            return instruments
            
        except Exception as e:
            logger.error(f"❌ Error loading cache: {e}")
            return None
    
    def load_instruments(self):
        """Load instruments from cache or download if not available."""
        # Try loading from cache first
        instruments = self._load_cache()
        
        if not instruments:
            logger.info("📥 Cache not found, downloading instruments...")
            if self.download_instruments():
                instruments = self._load_cache()
            else:
                logger.error("❌ Failed to load instruments")
                return
        
        # Build mappings
        self._build_mappings(instruments)
    
    def _build_mappings(self, instruments: List[Dict]):
        """Build symbol to security ID mappings."""
        try:
            for instrument in instruments:
                # Extract relevant fields
                # Dhan CSV format: SEM_EXM_EXCH_ID, SEM_SMST_SECURITY_ID, SEM_TRADING_SYMBOL, etc.
                exchange = instrument.get('SEM_EXM_EXCH_ID', '')
                security_id = instrument.get('SEM_SMST_SECURITY_ID', '')
                symbol = instrument.get('SEM_TRADING_SYMBOL', '')
                instrument_type = instrument.get('SEM_INSTRUMENT_NAME', '')
                
                # We're interested in NSE Equity (NSE) instruments
                if exchange == 'NSE' and instrument_type == 'EQUITY':
                    # Clean symbol (remove -EQ suffix if present)
                    clean_symbol = symbol.replace('-EQ', '').strip()
                    
                    self.symbol_to_security_id[clean_symbol] = security_id
                    self.instruments[security_id] = {
                        'symbol': clean_symbol,
                        'security_id': security_id,
                        'exchange': exchange,
                        'instrument_type': instrument_type,
                        'full_data': instrument
                    }
            
            logger.info(f"✅ Built mappings for {len(self.symbol_to_security_id)} NSE Equity symbols")
            
        except Exception as e:
            logger.error(f"❌ Error building mappings: {e}")
    
    def get_security_id(self, symbol: str) -> Optional[str]:
        """Get Dhan security ID for a given symbol."""
        return self.symbol_to_security_id.get(symbol.upper())
    
    def get_security_ids(self, symbols: List[str]) -> Dict[str, str]:
        """Get Dhan security IDs for multiple symbols."""
        result = {}
        for symbol in symbols:
            security_id = self.get_security_id(symbol)
            if security_id:
                result[symbol] = security_id
        return result
    
    def get_instrument_info(self, security_id: str) -> Optional[Dict]:
        """Get full instrument information for a security ID."""
        return self.instruments.get(security_id)


# Create singleton instance
dhan_instruments = DhanInstruments()


if __name__ == "__main__":
    """Test the Dhan instruments mapper."""
    from dotenv import load_dotenv
    load_dotenv()
    
    print("\n" + "="*60)
    print("🧪 TESTING DHAN INSTRUMENTS MAPPER")
    print("="*60 + "\n")
    
    # Test 1: Download and load instruments
    print("📥 Test 1: Loading Dhan Instruments...")
    dhan_instruments.download_instruments()
    dhan_instruments.load_instruments()
    print()
    
    # Test 2: Map some common symbols
    print("🔍 Test 2: Mapping Stock Symbols to Security IDs...")
    test_symbols = ["TCS", "RELIANCE", "INFY", "HDFCBANK", "ICICIBANK", "SBIN"]
    
    for symbol in test_symbols:
        security_id = dhan_instruments.get_security_id(symbol)
        if security_id:
            print(f"   ✅ {symbol:12} → Security ID: {security_id}")
        else:
            print(f"   ❌ {symbol:12} → Not found")
    
    print()
    
    # Test 3: Batch mapping
    print("📊 Test 3: Batch Mapping...")
    security_ids = dhan_instruments.get_security_ids(test_symbols)
    print(f"   Mapped {len(security_ids)}/{len(test_symbols)} symbols")
    print()
    
    # Test 4: Read symbols from watchlist file
    print("📋 Test 4: Mapping Watchlist Symbols...")
    watchlist_file = "nse_fo_stock_symbols.txt"
    
    if os.path.exists(watchlist_file):
        with open(watchlist_file, 'r') as f:
            content = f.read()
            # Parse comma-separated symbols
            symbols = [s.strip().strip('"') for s in content.split(',')]
            # Filter out test symbols
            symbols = [s for s in symbols if not s.startswith('0') and s]
        
        print(f"   Found {len(symbols)} symbols in watchlist")
        
        # Map first 10 symbols as test
        test_batch = symbols[:10]
        mapped = dhan_instruments.get_security_ids(test_batch)
        
        print(f"   Sample mapping (first 10):")
        for symbol in test_batch:
            security_id = mapped.get(symbol)
            if security_id:
                print(f"      ✅ {symbol:15} → {security_id}")
            else:
                print(f"      ❌ {symbol:15} → Not found")
        
        print(f"\n   Total mapped: {len(mapped)}/{len(test_batch)}")
    else:
        print(f"   ⚠️  Watchlist file not found: {watchlist_file}")
    
    print()
    print("="*60)
    print("🏁 TESTING COMPLETE")
    print("="*60 + "\n")

